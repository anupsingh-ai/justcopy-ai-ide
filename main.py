"""
Main application server that orchestrates the AI-powered IDE
"""
import os
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import aiofiles
import requests
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import git

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Kimi K2 IDE", description="AI-Powered Development Environment")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize components
embedding_model = None
vector_db = None
vllm_base_url = "http://localhost:8000"

# Data models
class ChatMessage(BaseModel):
    role: str
    content: str

class CodeRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    file_path: Optional[str] = None

class FileOperation(BaseModel):
    operation: str  # read, write, delete, list
    path: str
    content: Optional[str] = None

class ProjectRequest(BaseModel):
    name: str
    description: str
    template: Optional[str] = "basic"

# Global variables
projects_dir = Path("/app/data/projects")
vector_db_path = "/app/data/vector_db"

async def initialize_components():
    """Initialize embedding model and vector database"""
    global embedding_model, vector_db
    
    try:
        # Initialize embedding model
        logger.info("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector database
        logger.info("Initializing vector database...")
        vector_db = chromadb.PersistentClient(path=vector_db_path)
        
        # Create default collection for code context
        try:
            collection = vector_db.get_collection("code_context")
        except:
            collection = vector_db.create_collection("code_context")
        
        logger.info("Components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    await initialize_components()
    
    # Ensure projects directory exists
    projects_dir.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    """Serve the main interface"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "embedding_model": embedding_model is not None,
            "vector_db": vector_db is not None,
            "vllm": await check_vllm_health()
        }
    }

async def check_vllm_health():
    """Check if vLLM server is healthy"""
    try:
        response = requests.get(f"{vllm_base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@app.post("/api/chat")
async def chat_with_ai(messages: List[ChatMessage]):
    """Chat with the Kimi K2 model"""
    try:
        # Prepare the request for vLLM
        payload = {
            "model": "kimi-k2",
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        response = requests.post(
            f"{vllm_base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=500, detail=f"vLLM API error: {response.text}")
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/code/generate")
async def generate_code(request: CodeRequest):
    """Generate code based on prompt and context"""
    try:
        # Get relevant context from vector database
        context = await get_relevant_context(request.prompt)
        
        # Prepare system prompt for code generation
        system_prompt = """You are an expert software developer. Generate high-quality, well-documented code based on the user's request. 
        Consider the provided context and follow best practices. Always include comments and explanations."""
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nRequest: {request.prompt}"}
        ]
        
        if request.context:
            messages.append({"role": "user", "content": f"Additional context: {request.context}"})
        
        # Call the AI model
        payload = {
            "model": "kimi-k2",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        response = requests.post(
            f"{vllm_base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_code = result["choices"][0]["message"]["content"]
            
            # Store the generated code in vector database for future context
            await store_code_context(request.prompt, generated_code)
            
            return {"code": generated_code, "context_used": context}
        else:
            raise HTTPException(status_code=500, detail=f"Code generation failed: {response.text}")
            
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_relevant_context(query: str, max_results: int = 5) -> str:
    """Get relevant context from vector database"""
    try:
        if not vector_db or not embedding_model:
            return ""
        
        collection = vector_db.get_collection("code_context")
        
        # Generate embedding for the query
        query_embedding = embedding_model.encode([query])
        
        # Search for similar content
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=max_results
        )
        
        # Combine relevant documents
        context_parts = []
        if results["documents"]:
            for doc in results["documents"][0]:
                context_parts.append(doc)
        
        return "\n\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        return ""

async def store_code_context(prompt: str, code: str):
    """Store code and prompt in vector database for future context"""
    try:
        if not vector_db or not embedding_model:
            return
        
        collection = vector_db.get_collection("code_context")
        
        # Create document content
        document = f"Prompt: {prompt}\n\nCode:\n{code}"
        
        # Generate embedding
        embedding = embedding_model.encode([document])
        
        # Store in vector database
        collection.add(
            documents=[document],
            embeddings=embedding.tolist(),
            ids=[f"code_{len(collection.get()['ids']) + 1}"]
        )
        
    except Exception as e:
        logger.error(f"Context storage error: {e}")

@app.post("/api/files/operation")
async def file_operation(request: FileOperation):
    """Perform file operations"""
    try:
        file_path = projects_dir / request.path.lstrip("/")
        
        if request.operation == "read":
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
            return {"content": content}
        
        elif request.operation == "write":
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(request.content or "")
            
            # Store file content in vector database for context
            await store_code_context(f"File: {request.path}", request.content or "")
            
            return {"message": "File written successfully"}
        
        elif request.operation == "delete":
            if file_path.exists():
                file_path.unlink()
            return {"message": "File deleted successfully"}
        
        elif request.operation == "list":
            if file_path.is_dir():
                items = []
                for item in file_path.iterdir():
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "path": str(item.relative_to(projects_dir))
                    })
                return {"items": items}
            else:
                raise HTTPException(status_code=400, detail="Path is not a directory")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
            
    except Exception as e:
        logger.error(f"File operation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create")
async def create_project(request: ProjectRequest):
    """Create a new project"""
    try:
        project_path = projects_dir / request.name
        
        if project_path.exists():
            raise HTTPException(status_code=400, detail="Project already exists")
        
        # Create project directory
        project_path.mkdir(parents=True)
        
        # Create basic project structure based on template
        if request.template == "python":
            await create_python_project(project_path, request)
        elif request.template == "javascript":
            await create_javascript_project(project_path, request)
        elif request.template == "web":
            await create_web_project(project_path, request)
        else:
            await create_basic_project(project_path, request)
        
        return {"message": f"Project '{request.name}' created successfully", "path": str(project_path)}
        
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_basic_project(project_path: Path, request: ProjectRequest):
    """Create a basic project structure"""
    # Create README
    readme_content = f"""# {request.name}

{request.description}

## Getting Started

This project was created with Kimi K2 IDE.

## Structure

- `src/` - Source code
- `docs/` - Documentation
- `tests/` - Test files
"""
    
    async with aiofiles.open(project_path / "README.md", 'w') as f:
        await f.write(readme_content)
    
    # Create basic directories
    (project_path / "src").mkdir()
    (project_path / "docs").mkdir()
    (project_path / "tests").mkdir()

async def create_python_project(project_path: Path, request: ProjectRequest):
    """Create a Python project structure"""
    await create_basic_project(project_path, request)
    
    # Create Python-specific files
    requirements_content = """# Add your dependencies here
requests>=2.25.0
"""
    
    async with aiofiles.open(project_path / "requirements.txt", 'w') as f:
        await f.write(requirements_content)
    
    main_py_content = f'''"""
{request.description}
"""

def main():
    print("Hello from {request.name}!")

if __name__ == "__main__":
    main()
'''
    
    async with aiofiles.open(project_path / "src" / "main.py", 'w') as f:
        await f.write(main_py_content)

async def create_javascript_project(project_path: Path, request: ProjectRequest):
    """Create a JavaScript project structure"""
    await create_basic_project(project_path, request)
    
    # Create package.json
    package_json = {
        "name": request.name.lower().replace(" ", "-"),
        "version": "1.0.0",
        "description": request.description,
        "main": "src/index.js",
        "scripts": {
            "start": "node src/index.js",
            "test": "echo \"Error: no test specified\" && exit 1"
        }
    }
    
    async with aiofiles.open(project_path / "package.json", 'w') as f:
        await f.write(json.dumps(package_json, indent=2))
    
    # Create main JavaScript file
    index_js_content = f'''/**
 * {request.description}
 */

console.log("Hello from {request.name}!");
'''
    
    async with aiofiles.open(project_path / "src" / "index.js", 'w') as f:
        await f.write(index_js_content)

async def create_web_project(project_path: Path, request: ProjectRequest):
    """Create a web project structure"""
    await create_basic_project(project_path, request)
    
    # Create HTML file
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{request.name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>{request.name}</h1>
    <p>{request.description}</p>
    <script src="script.js"></script>
</body>
</html>
'''
    
    async with aiofiles.open(project_path / "src" / "index.html", 'w') as f:
        await f.write(html_content)
    
    # Create CSS file
    css_content = '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}
'''
    
    async with aiofiles.open(project_path / "src" / "styles.css", 'w') as f:
        await f.write(css_content)
    
    # Create JavaScript file
    js_content = f'''// {request.description}

document.addEventListener('DOMContentLoaded', function() {{
    console.log('{request.name} loaded successfully!');
}});
'''
    
    async with aiofiles.open(project_path / "src" / "script.js", 'w') as f:
        await f.write(js_content)

@app.get("/api/projects/list")
async def list_projects():
    """List all projects"""
    try:
        projects = []
        for item in projects_dir.iterdir():
            if item.is_dir():
                projects.append({
                    "name": item.name,
                    "path": str(item.relative_to(projects_dir))
                })
        return {"projects": projects}
        
    except Exception as e:
        logger.error(f"Project listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message["type"] == "code_request":
                # Handle real-time code generation
                response = await generate_code(CodeRequest(**message["data"]))
                await websocket.send_text(json.dumps({
                    "type": "code_response",
                    "data": response
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=False,
        log_level="info"
    )
