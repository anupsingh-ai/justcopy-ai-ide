# 🤖 JustCopy AI IDE

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![GPU](https://img.shields.io/badge/GPU-Accelerated-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Local](https://img.shields.io/badge/100%25-Local-brightgreen.svg)](https://github.com)
[![Free](https://img.shields.io/badge/Unlimited-Tokens-gold.svg)](https://github.com)

A **completely local AI IDE** that runs powerful LLM models on your machine for unlimited, lightning-fast code generation - **completely free**!

> ⚡ **Lightning Fast**: Local models = zero latency + unlimited tokens
> 🔒 **100% Private**: Your code never leaves your machine
> 💰 **Completely Free**: No API costs, no token limits, no subscriptions

**Maintained by [JustCopy.ai](https://justcopy.ai) - The AI-powered website copying platform**

![JustCopy AI IDE Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=JustCopy+AI+IDE+Demo)

## ✨ Why JustCopy AI IDE?

⚡ **Lightning Fast**: No API calls = instant responses (10x faster than cloud APIs)
💰 **Unlimited & Free**: No token limits, no monthly bills, no usage restrictions
🔒 **100% Private**: Your code stays on your machine - perfect for proprietary projects
🎯 **Always Available**: No internet required, no rate limits, no downtime
🚀 **GPU Accelerated**: Harness your local GPU power for maximum performance

## 🚀 Features

🤖 **Local LLM Models**: Run powerful models like Kimi K2, CodeLlama, and more locally
💻 **Web-based IDE**: VS Code Server accessible through your browser
🔍 **Smart Context**: Local vector database with embeddings for intelligent code context
📦 **Self-contained**: Everything runs in a single Docker container
🔧 **Multi-Model Support**: Switch between different LLM models based on your needs

## 🚀 Quick Start

### Prerequisites

- Docker with NVIDIA runtime support
- NVIDIA GPU with CUDA support (recommended for best performance)
- 8GB+ RAM (16GB+ recommended for larger models)
- **Hugging Face Token** (free account required - [Get one here](https://huggingface.co/settings/tokens))

> 🤔 **Why do I need a Hugging Face token?**
> - Downloads AI models from Hugging Face Hub (like Kimi K2, CodeLlama, etc.)
> - Without token: Slow downloads + rate limits
> - With token: Fast downloads + no limits
> - **It's completely free** - just sign up at [huggingface.co](https://huggingface.co)

### 1. Clone and Setup

```bash
git clone https://github.com/anupsingh-ai/justcopy-ai-ide.git
cd justcopy-ai-ide
cp .env.example .env
```

### 2. Get Your Free Hugging Face Token

1. **Sign up** at [huggingface.co](https://huggingface.co) (completely free)
2. **Go to Settings** → [Access Tokens](https://huggingface.co/settings/tokens)
3. **Create New Token** → Select "Read" permissions
4. **Copy the token** and add it to `.env` file:

```bash
# Replace with your actual token from Hugging Face
HUGGING_FACE_HUB_TOKEN=hf_your_actual_token_here
```

> 💡 **Pro tip**: This token allows downloading models up to 10x faster and without rate limits!

### 3. Build and Run

```bash
# Using the automated build script (recommended)
./build.sh
./run.sh

# Or using Docker Compose
docker-compose up --build

# Or using Docker directly
docker build -t local-coding-agent .
docker run --runtime nvidia --gpus all \
  --name local-coding-agent \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 8888:8888 \
  --ipc=host \
  local-coding-agent
```

### 4. Access Your JustCopy AI IDE

Once all services are running, access:

- **💻 Main Interface**: http://localhost:8888 (Start here!)
- **🔗 VS Code IDE**: http://localhost:8080
- **🤖 AI Assistant API**: http://localhost:8888/api
- **🧠 Local LLM API**: http://localhost:8000

> ✨ **First time?** Start at http://localhost:8888 for the main interface with AI chat and project management!

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

## ❓ Frequently Asked Questions

### Why do I need a Hugging Face token?

**TL;DR**: To download AI models faster and without limits (it's free!)

**Detailed explanation**:
- 🤖 **Model Downloads**: JustCopy AI IDE downloads powerful AI models (Kimi K2, CodeLlama, etc.) from Hugging Face Hub
- 🐌 **Without Token**: Downloads are slow (1-2 MB/s) and heavily rate-limited
- ⚡ **With Token**: Downloads are 10x faster (20+ MB/s) with no rate limits
- 💰 **Cost**: Completely FREE - just requires a free Hugging Face account
- 🔒 **Security**: Token only has "Read" permissions - cannot modify anything

### What models does it download?
- **Kimi K2 Instruct**: Main coding assistant model (~7GB)
- **Sentence Transformers**: For code context understanding (~400MB)
- **Additional Models**: You can add CodeLlama, Mistral, etc. later

### Can I use it without a token?
**No** - the models are required for the AI functionality. But getting a token takes just 2 minutes:
1. Sign up at [huggingface.co](https://huggingface.co) (free)
2. Go to Settings → [Access Tokens](https://huggingface.co/settings/tokens)
3. Create token with "Read" permissions
4. Add to `.env` file

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
- 🐛 [Report Issues](https://github.com/anupsingh-ai/justcopy-ai-ide/issues)
- 💬 [Start Discussions](https://github.com/anupsingh-ai/justcopy-ai-ide/discussions)
- ⭐ Star the repository if you find it useful!

---

**Maintained by [JustCopy.ai](https://justcopy.ai) | Created by [Anup Singh](https://github.com/anupsingh-ai)**

*Empowering developers with AI-powered coding assistance*
