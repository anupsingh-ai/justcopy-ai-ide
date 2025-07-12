# 🤖 Kimi K2 AI-Powered IDE

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![GPU](https://img.shields.io/badge/GPU-Accelerated-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

A **self-contained Docker environment** that provides an AI-powered development experience with the Kimi K2 Instruct model, VS Code Server, and local vector database for intelligent code assistance.

> 🚀 **One-command setup**: Get a complete AI development environment running in minutes!

![Kimi K2 IDE Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=Kimi+K2+AI+IDE+Demo)

## Features

🤖 **AI-Powered Coding**: Kimi K2 Instruct model for intelligent code generation and assistance
💻 **Web-based IDE**: VS Code Server accessible through your browser
🔍 **Smart Context**: Local vector database with embeddings for intelligent code context
📦 **Self-contained**: Everything runs in a single Docker container
🚀 **GPU Accelerated**: Optimized for NVIDIA GPUs with CUDA support

## 🚀 Quick Start

### Prerequisites

- Docker with NVIDIA runtime support
- NVIDIA GPU with CUDA support (optional, CPU fallback available)
- Hugging Face account and token ([Get one here](https://huggingface.co/settings/tokens))

### 1. Clone and Setup

```bash
git clone https://github.com/anupsingh-ai/findy-coding-ai-agent.git
cd findy-coding-ai-agent
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file and add your Hugging Face token:

```bash
HUGGING_FACE_HUB_TOKEN=your_actual_token_here
```

### 3. Build and Run

```bash
# Using Docker Compose (recommended)
docker-compose up --build

# Or using Docker directly
docker build -t kimi-k2-ide .
docker run --runtime nvidia --gpus all \
  --name kimi-k2-ide \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 8888:8888 \
  --ipc=host \
  kimi-k2-ide
```

### 4. Access Your Development Environment

Once all services are running, access:

- **🔗 VS Code IDE**: http://localhost:8080
- **🤖 AI Assistant API**: http://localhost:8888
- **🧠 vLLM API**: http://localhost:8000

## Usage

### Using the IDE

1. Open http://localhost:8080 in your browser
2. Start coding in the integrated VS Code environment
3. Your projects are automatically saved in the `data/projects` directory

### AI-Powered Features

#### Code Generation
```bash
curl -X POST "http://localhost:8888/api/code/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to calculate fibonacci numbers",
    "context": "I need an efficient implementation"
  }'
```

#### Chat with AI
```bash
curl -X POST "http://localhost:8888/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "How do I optimize this Python code for better performance?"
      }
    ]
  }'
```

#### Project Management
```bash
# Create a new project
curl -X POST "http://localhost:8888/api/projects/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-web-app",
    "description": "A modern web application",
    "template": "web"
  }'

# List projects
curl "http://localhost:8888/api/projects/list"
```

### File Operations
```bash
# Read a file
curl -X POST "http://localhost:8888/api/files/operation" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "read",
    "path": "my-project/src/main.py"
  }'

# Write a file
curl -X POST "http://localhost:8888/api/files/operation" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "write",
    "path": "my-project/src/main.py",
    "content": "print(\"Hello, World!\")"
  }'
```

## Project Templates

The IDE supports several project templates:

- **basic**: Simple project structure with README and basic directories
- **python**: Python project with requirements.txt and main.py
- **javascript**: Node.js project with package.json and index.js
- **web**: Web project with HTML, CSS, and JavaScript files

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   vLLM      │  │  VS Code    │  │    Main API         │  │
│  │   Server    │  │  Server     │  │    (FastAPI)        │  │
│  │   :8000     │  │   :8080     │  │     :8888           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  ChromaDB   │  │ Embeddings  │  │    File System      │  │
│  │  Vector DB  │  │   Model     │  │    /app/data        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Health Check
- `GET /health` - Check service status

### AI Chat
- `POST /api/chat` - Chat with Kimi K2 model

### Code Generation
- `POST /api/code/generate` - Generate code with context

### File Operations
- `POST /api/files/operation` - Perform file operations (read/write/delete/list)

### Project Management
- `POST /api/projects/create` - Create new project
- `GET /api/projects/list` - List all projects

### WebSocket
- `WS /ws` - Real-time communication for live coding assistance

## Data Persistence

All data is persisted in the `data/` directory:

- `data/projects/` - Your code projects
- `data/vector_db/` - Vector database for code context
- `data/embeddings/` - Cached embeddings

## Troubleshooting

### GPU Issues
```bash
# Check GPU availability
nvidia-smi

# Verify Docker NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Memory Issues
If you encounter out-of-memory errors, adjust the GPU memory utilization:

```bash
# Edit the start.sh script and modify:
--gpu-memory-utilization 0.5  # Reduce from 0.7 to 0.5
```

### Model Download Issues
Ensure your Hugging Face token has the necessary permissions:

```bash
# Test token access
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://huggingface.co/api/whoami
```

## Development

### Building from Source
```bash
docker build -t kimi-k2-ide .
```

### Running in Development Mode
```bash
# Mount source code for development
docker run --runtime nvidia --gpus all \
  -v $(pwd):/app \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 -p 8080:8080 -p 8888:8888 \
  --env-file .env \
  kimi-k2-ide
```

## 🌟 Star History

⭐ **Star this repository** if you find it useful!

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Ways to Contribute
- 🐛 Report bugs
- 💡 Suggest features  
- 📝 Improve documentation
- 🔧 Submit code improvements
- 🧪 Add tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Moonshot AI](https://www.moonshot.cn/) for the Kimi K2 Instruct model
- [vLLM](https://github.com/vllm-project/vllm) for fast inference
- [Code Server](https://github.com/coder/code-server) for the web IDE
- [ChromaDB](https://github.com/chroma-core/chroma) for vector database
- The open source community for inspiration and tools

## 📞 Support

- 📖 Check the [Usage Guide](USAGE.md)
- 🐛 [Report Issues](https://github.com/anupsingh-ai/findy-coding-ai-agent/issues)
- 💬 [Start Discussions](https://github.com/anupsingh-ai/findy-coding-ai-agent/discussions)
- ⭐ Star the repository if you find it useful!

---

**Made with ❤️ by [Anup Singh](https://github.com/anupsingh-ai)**

*Empowering developers with AI-powered coding assistance*
