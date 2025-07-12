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
app = FastAPI(
    title="JustCopy AI IDE",
    description="Lightning-fast local AI IDE with unlimited tokens - completely free!",
    version="1.0.0"
)

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

# Old chat endpoint removed - using agentic chat endpoint instead

class AgenticChatRequest(BaseModel):
    message: str
    project_path: str = "/app/data/projects"

class AgenticChatResponse(BaseModel):
    response: str
    file_operations: List[Dict[str, Any]] = []
    files_modified: bool = False

class FolderSelectionRequest(BaseModel):
    folder_path: str
    file_count: int = 0

class FolderSelectionResponse(BaseModel):
    message: str
    folder_path: str
    success: bool = True

@app.post("/api/chat", response_model=AgenticChatResponse)
async def agentic_chat(request: AgenticChatRequest):
    """Agentic chat interface that can modify files based on user requests"""
    try:
        # Analyze the user's request to determine intent
        intent = await analyze_user_intent(request.message)
        
        # Get current project structure
        project_files = await get_project_structure(request.project_path)
        
        # Prepare system prompt for agentic behavior
        system_prompt = f"""You are an AI coding agent that can create, modify, and manage files. 
        You have access to the following project directory: {request.project_path}
        
        Current project structure:
        {project_files}
        
        Based on the user's request, you should:
        1. Understand what they want to accomplish
        2. Determine what files need to be created or modified
        3. Generate the appropriate code
        4. Provide clear explanations of what you're doing
        
        Always be helpful, accurate, and explain your actions clearly.
        If you need to create or modify files, describe exactly what you're doing.
        
        User request: {request.message}
        
        Respond with a helpful explanation and indicate any file operations you would perform.
        """
        
        # Call the AI model
        payload = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
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
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # Parse the AI response to extract file operations
            file_operations = await extract_file_operations(ai_response, request.message)
            
            # Execute file operations if any
            files_modified = False
            if file_operations:
                files_modified = await execute_file_operations(file_operations, request.project_path)
            
            return AgenticChatResponse(
                response=ai_response,
                file_operations=file_operations,
                files_modified=files_modified
            )
        else:
            # Fallback response if AI service is not available
            return AgenticChatResponse(
                response="I understand you want to work on your code. However, the AI service is currently unavailable. Please try again later or check the service status.",
                file_operations=[],
                files_modified=False
            )
            
    except Exception as e:
        logger.error(f"Agentic chat error: {e}")
        return AgenticChatResponse(
            response=f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your request.",
            file_operations=[],
            files_modified=False
        )

@app.post("/api/folder/select", response_model=FolderSelectionResponse)
async def select_folder(request: FolderSelectionRequest):
    """Handle folder selection from the frontend"""
    try:
        logger.info(f"Folder selected: {request.folder_path} with {request.file_count} files")
        
        # Validate folder path (basic security check)
        if not request.folder_path or '..' in request.folder_path:
            raise HTTPException(status_code=400, detail="Invalid folder path")
        
        # Create a friendly response message
        if request.file_count > 0:
            message = f"Great! I've selected the folder '{request.folder_path}' with {request.file_count} files. I'm ready to help you work with your code!"
        else:
            message = f"Folder '{request.folder_path}' selected. I'm ready to help you create new files and projects in this directory!"
        
        return FolderSelectionResponse(
            message=message,
            folder_path=request.folder_path,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Folder selection error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select folder: {str(e)}")

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

@app.get("/api/files/list")
async def list_files(path: str = "/app/data/projects"):
    """List files in a directory"""
    try:
        directory = Path(path)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            return {"files": []}
        
        files = []
        for item in directory.iterdir():
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item),
                "size": item.stat().st_size if item.is_file() else 0
            })
        
        return {"files": files}
        
    except Exception as e:
        logger.error(f"File listing error: {e}")
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

# Helper functions for agentic chat
async def analyze_user_intent(message: str) -> str:
    """Analyze user's message to determine their intent"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['create', 'make', 'build', 'generate']):
        return 'create'
    elif any(word in message_lower for word in ['modify', 'change', 'update', 'edit', 'fix']):
        return 'modify'
    elif any(word in message_lower for word in ['delete', 'remove']):
        return 'delete'
    elif any(word in message_lower for word in ['show', 'list', 'display']):
        return 'read'
    else:
        return 'general'

async def get_project_structure(project_path: str) -> str:
    """Get the current project structure as a string"""
    try:
        project_dir = Path(project_path)
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            return "Empty project directory (just created)"
        
        structure = []
        for item in project_dir.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(project_dir)
                structure.append(f"📄 {relative_path}")
            elif item.is_dir() and item != project_dir:
                relative_path = item.relative_to(project_dir)
                structure.append(f"📁 {relative_path}/")
        
        if not structure:
            return "Empty project directory"
        
        return "\n".join(structure[:20])  # Limit to first 20 items
    except Exception as e:
        logger.error(f"Error getting project structure: {e}")
        return "Could not read project structure"

async def extract_file_operations(ai_response: str, user_message: str) -> List[Dict[str, Any]]:
    """Extract file operations from AI response and user message"""
    operations = []
    
    # Simple pattern matching for file operations
    user_lower = user_message.lower()
    
    # Detect file creation requests
    if any(word in user_lower for word in ['create', 'make', 'build', 'generate']):
        if 'python' in user_lower:
            operations.append({
                "operation": "CREATE",
                "file_path": "main.py",
                "description": "Creating Python file based on request"
            })
        elif 'react' in user_lower or 'javascript' in user_lower:
            operations.append({
                "operation": "CREATE",
                "file_path": "App.js",
                "description": "Creating React/JavaScript file based on request"
            })
        elif 'html' in user_lower or 'web' in user_lower:
            operations.append({
                "operation": "CREATE",
                "file_path": "index.html",
                "description": "Creating HTML file based on request"
            })
        else:
            operations.append({
                "operation": "CREATE",
                "file_path": "new_file.txt",
                "description": "Creating file based on request"
            })
    
    return operations

async def execute_file_operations(operations: List[Dict[str, Any]], project_path: str) -> bool:
    """Execute the file operations"""
    try:
        project_dir = Path(project_path)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        for operation in operations:
            if operation["operation"] == "CREATE":
                file_path = project_dir / operation["file_path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Generate appropriate content based on file type
                content = await generate_file_content(operation["file_path"], operation.get("description", ""))
                
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(content)
                
                logger.info(f"Created file: {file_path}")
        
        return len(operations) > 0
    except Exception as e:
        logger.error(f"Error executing file operations: {e}")
        return False

async def generate_file_content(file_path: str, description: str) -> str:
    """Generate appropriate content for a file based on its type"""
    file_name = Path(file_path).name.lower()
    
    if file_name.endswith('.py'):
        return f'''#!/usr/bin/env python3
"""
{description}
"""

def main():
    """Main function"""
    print("Hello from {file_name}!")
    # TODO: Implement your code here
    pass

if __name__ == "__main__":
    main()
'''
    elif file_name.endswith('.js') or file_name.endswith('.jsx'):
        return f'''/**
 * {description}
 */

console.log("Hello from {file_name}!");

// TODO: Implement your code here
'''
    elif file_name.endswith('.html'):
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated HTML</title>
</head>
<body>
    <h1>Generated HTML File</h1>
    <p>{description}</p>
    <!-- TODO: Add your content here -->
</body>
</html>
'''
    elif file_name.endswith('.css'):
        return f'''/* {description} */

body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}}

/* TODO: Add your styles here */
'''
    else:
        return f'''# {description}

This file was generated by the Local Coding Agent.

TODO: Add your content here
'''

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=False,
        log_level="info"
    )
