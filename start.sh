#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting JustCopy AI IDE...${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        echo -e "${YELLOW}   Attempt $attempt/$max_attempts - $service_name not ready yet...${NC}"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Start ChromaDB vector database
echo -e "${GREEN}📊 Starting ChromaDB vector database...${NC}"
cd /app && python3 -c "
import chromadb
from chromadb.config import Settings
client = chromadb.PersistentClient(path='/app/data/vector_db')
print('ChromaDB initialized successfully')
" &

# Start vLLM server for Kimi K2 model
echo -e "${GREEN}🤖 Starting vLLM server with Kimi K2 Instruct model...${NC}"
python3 -m vllm.entrypoints.openai.api_server \
    --model moonshotai/Kimi-K2-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.7 \
    --max-model-len 4096 \
    --served-model-name kimi-k2 &

# Wait for vLLM to be ready
wait_for_service "http://localhost:8000/health" "vLLM API Server"

# Start the main application API
echo -e "${GREEN}🔧 Starting main application API...${NC}"
cd /app && python3 main.py &

# Wait for main API to be ready
wait_for_service "http://localhost:8888/health" "Main API Server"

# Start VS Code Server
echo -e "${GREEN}💻 Starting VS Code Server...${NC}"
code-server \
    --bind-addr 0.0.0.0:8080 \
    --auth none \
    --disable-telemetry \
    --disable-update-check \
    /app/data/projects &

# Wait for VS Code Server to be ready
wait_for_service "http://localhost:8080" "VS Code Server"

echo -e "${GREEN}🎉 JustCopy AI IDE started successfully!${NC}"
echo -e "${GREEN}📝 Access your local AI coding environment at:${NC}"
echo -e "   💻 Main Interface: http://localhost:8888 (Start here!)"
echo -e "   🔗 VS Code IDE: http://localhost:8080"
echo -e "   🤖 Local LLM API: http://localhost:8000"
echo -e ""
echo -e "${YELLOW}⚡ Local Benefits:${NC}"
echo -e "   • Lightning fast responses (no API delays)"
echo -e "   • Unlimited tokens - code as much as you want!"
echo -e "   • 100% private - your code stays on your machine"
echo -e "   • Completely free - no subscription fees"
echo -e "   • Works offline - no internet required"
echo -e ""

# Keep the container running
wait
