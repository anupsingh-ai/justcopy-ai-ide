#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Kimi K2 AI IDE${NC}"
echo -e "${BLUE}========================${NC}"

# Check if image exists
if ! docker image inspect kimi-k2-ide > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker image not found. Building first...${NC}"
    ./build.sh || exit 1
fi

# Stop existing container if running
if docker ps -q -f name=kimi-k2-ide | grep -q .; then
    echo -e "${YELLOW}⏹️  Stopping existing container...${NC}"
    docker stop kimi-k2-ide
    docker rm kimi-k2-ide
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❗ .env file not found. Please run ./build.sh first.${NC}"
    exit 1
fi

# Run the container
echo -e "${GREEN}🚀 Starting container...${NC}"

# Check if GPU is available
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo -e "${GREEN}🎮 GPU detected - running with GPU acceleration${NC}"
    docker run -d \
        --name kimi-k2-ide \
        --runtime nvidia \
        --gpus all \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -v $(pwd)/data:/app/data \
        --env-file .env \
        -p 8000:8000 \
        -p 8080:8080 \
        -p 8888:8888 \
        --ipc=host \
        --shm-size=2g \
        kimi-k2-ide
else
    echo -e "${YELLOW}⚠️  No GPU detected - running in CPU mode${NC}"
    docker run -d \
        --name kimi-k2-ide \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -v $(pwd)/data:/app/data \
        --env-file .env \
        -p 8000:8000 \
        -p 8080:8080 \
        -p 8888:8888 \
        --shm-size=2g \
        kimi-k2-ide
fi

# Wait for container to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if container is running
if docker ps -q -f name=kimi-k2-ide | grep -q .; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${GREEN}📝 Access your development environment at:${NC}"
    echo -e "   🌐 Main Interface: ${BLUE}http://localhost:8888${NC}"
    echo -e "   💻 VS Code IDE: ${BLUE}http://localhost:8080${NC}"
    echo -e "   🤖 AI API: ${BLUE}http://localhost:8000${NC}"
    echo -e ""
    echo -e "${GREEN}📊 View logs with: ${BLUE}docker logs -f kimi-k2-ide${NC}"
    echo -e "${GREEN}🛑 Stop with: ${BLUE}docker stop kimi-k2-ide${NC}"
    echo -e ""
    echo -e "${YELLOW}💡 Tip: It may take a few minutes for all services to be ready${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    echo -e "${RED}📊 Check logs with: docker logs kimi-k2-ide${NC}"
    exit 1
fi
