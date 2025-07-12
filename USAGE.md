# Kimi K2 AI IDE Usage Guide

## Quick Start

### 1. Setup
```bash
# Clone the repository
git clone <repository-url>
cd kimi

# Copy environment template
cp .env.example .env

# Edit .env and add your Hugging Face token
nano .env  # or use your preferred editor
```

### 2. Build and Run
```bash
# Build the Docker image
./build.sh

# Run the container
./run.sh

# Or use Docker Compose
docker-compose up --build
```

### 3. Access Your IDE
- **Main Interface**: http://localhost:8888
- **VS Code IDE**: http://localhost:8080
- **AI API**: http://localhost:8000

## Features Overview

### 🤖 AI-Powered Code Generation

The IDE integrates the Kimi K2 Instruct model for intelligent code assistance:

#### Chat with AI
```bash
curl -X POST "http://localhost:8888/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "How do I create a REST API in Python using FastAPI?"
      }
    ]
  }'
```

#### Generate Code
```bash
curl -X POST "http://localhost:8888/api/code/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to validate email addresses",
    "context": "I need input validation for a web form"
  }'
```

### 💻 VS Code IDE Features

The web-based VS Code instance includes:

- **Syntax Highlighting**: For 100+ programming languages
- **IntelliSense**: Code completion and suggestions
- **Debugging**: Built-in debugger support
- **Extensions**: Pre-installed development extensions
- **Git Integration**: Full Git support with visual diff
- **Terminal**: Integrated terminal for command-line operations

### 📁 Project Management

#### Create Projects
```bash
# Python project
curl -X POST "http://localhost:8888/api/projects/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-python-app",
    "description": "A Python web application",
    "template": "python"
  }'

# Web project
curl -X POST "http://localhost:8888/api/projects/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-website",
    "description": "A modern website",
    "template": "web"
  }'
```

#### Available Templates
- **basic**: Simple project structure
- **python**: Python project with requirements.txt
- **javascript**: Node.js project with package.json
- **web**: HTML/CSS/JavaScript web project

### 🔍 Smart Context Search

The IDE uses a local vector database to provide intelligent context:

- **Automatic Indexing**: Your code is automatically indexed
- **Semantic Search**: Find relevant code based on meaning
- **Context-Aware Generation**: AI uses your existing code as context

### 📊 File Operations

#### Read Files
```bash
curl -X POST "http://localhost:8888/api/files/operation" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "read",
    "path": "my-project/src/main.py"
  }'
```

#### Write Files
```bash
curl -X POST "http://localhost:8888/api/files/operation" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "write",
    "path": "my-project/src/utils.py",
    "content": "def hello_world():\n    print(\"Hello, World!\")"
  }'
```

#### List Directory
```bash
curl -X POST "http://localhost:8888/api/files/operation" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "list",
    "path": "my-project"
  }'
```

## Workflow Examples

### Example 1: Creating a Python Web API

1. **Create Project**:
   ```bash
   curl -X POST "http://localhost:8888/api/projects/create" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "todo-api",
       "description": "A TODO list API",
       "template": "python"
     }'
   ```

2. **Generate API Code**:
   ```bash
   curl -X POST "http://localhost:8888/api/code/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Create a FastAPI application with CRUD operations for a TODO list",
       "context": "I need endpoints for creating, reading, updating, and deleting TODO items"
     }'
   ```

3. **Open in IDE**: Navigate to http://localhost:8080 and open the project

4. **Edit and Test**: Use the IDE to refine the code and test it

### Example 2: Building a React Component

1. **Create Web Project**:
   ```bash
   curl -X POST "http://localhost:8888/api/projects/create" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "react-dashboard",
       "description": "A React dashboard component",
       "template": "web"
     }'
   ```

2. **Generate Component**:
   ```bash
   curl -X POST "http://localhost:8888/api/code/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Create a React dashboard component with charts and metrics",
       "context": "I need a responsive dashboard with data visualization"
     }'
   ```

3. **Iterate**: Use the AI to refine and improve the component

## Tips and Best Practices

### 🎯 Effective AI Prompts

**Good Prompts**:
- "Create a Python function to validate email addresses using regex"
- "Build a REST API endpoint for user authentication with JWT tokens"
- "Generate a React component for a responsive navigation menu"

**Less Effective Prompts**:
- "Write code"
- "Help me"
- "Fix this"

### 🔧 Development Workflow

1. **Start with AI**: Use AI to generate initial code structure
2. **Refine in IDE**: Use VS Code to edit and improve the code
3. **Test Iteratively**: Run and test your code frequently
4. **Use Context**: Let the AI learn from your existing codebase

### 📚 Learning Resources

- **AI Chat**: Ask the AI to explain concepts or code
- **Code Generation**: Generate examples to learn from
- **Documentation**: Use AI to generate documentation for your code

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check Docker logs
docker logs kimi-k2-ide

# Verify GPU access (if using GPU)
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### AI Responses Are Slow
- **GPU Memory**: Reduce `--gpu-memory-utilization` in start.sh
- **Model Size**: The Kimi K2 model is large and requires significant resources
- **CPU Mode**: Consider running without GPU if memory is limited

#### VS Code Won't Load
```bash
# Check if port 8080 is available
lsof -i :8080

# Restart the container
docker restart kimi-k2-ide
```

#### Out of Memory Errors
```bash
# Increase Docker memory limit
# Edit Docker Desktop settings or add --memory flag
docker run --memory=8g ...
```

### Performance Optimization

#### For GPU Systems
- Ensure NVIDIA drivers are up to date
- Use `nvidia-smi` to monitor GPU usage
- Adjust `--gpu-memory-utilization` based on your GPU memory

#### For CPU Systems
- Increase `--shm-size` for better performance
- Consider using a smaller model if available
- Close unnecessary applications to free memory

## Advanced Usage

### Custom Extensions

Add your own VS Code extensions by editing `vscode-extensions.txt`:

```bash
# Add your extension
echo "your-publisher.your-extension" >> vscode-extensions.txt

# Rebuild the image
./build.sh
```

### Custom Models

To use a different model, edit the `start.sh` script:

```bash
# Change the model name
--model your-custom-model-name
```

### API Integration

Integrate the AI capabilities into your own applications:

```python
import requests

def generate_code(prompt, context=""):
    response = requests.post(
        "http://localhost:8888/api/code/generate",
        json={
            "prompt": prompt,
            "context": context
        }
    )
    return response.json()["code"]

# Use it in your application
code = generate_code("Create a function to sort a list", "Python")
print(code)
```

## Support and Contributing

### Getting Help
- Check the logs: `docker logs kimi-k2-ide`
- Run the test script: `python3 test.py`
- Review this documentation

### Contributing
1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

### Reporting Issues
When reporting issues, please include:
- Your system specifications
- Docker version
- Error logs
- Steps to reproduce

---

**Happy Coding with Kimi K2 AI IDE! 🚀**
