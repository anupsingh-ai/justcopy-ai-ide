#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 JustCopy AI IDE Builder${NC}"
echo -e "${BLUE}=========================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please edit .env file and add your HUGGING_FACE_HUB_TOKEN${NC}"
    echo -e "${RED}❗ Then run this script again.${NC}"
    exit 1
fi

# Check if HUGGING_FACE_HUB_TOKEN is set
source .env
if [ -z "$HUGGING_FACE_HUB_TOKEN" ] || [ "$HUGGING_FACE_HUB_TOKEN" = "your_huggingface_token_here" ] || [ "$HUGGING_FACE_HUB_TOKEN" = "hf_your_actual_token_here" ]; then
    echo -e "${RED}❗ HUGGING_FACE_HUB_TOKEN is not set in .env file${NC}"
    echo -e "${YELLOW}💡 Why do you need this token?${NC}"
    echo -e "   • Downloads AI models from Hugging Face Hub (Kimi K2, CodeLlama, etc.)"
    echo -e "   • Without token: Slow downloads + rate limits"
    echo -e "   • With token: Fast downloads + no limits"
    echo -e "   • It's completely FREE - just sign up!"
    echo -e ""
    echo -e "${GREEN}🚀 Quick setup:${NC}"
    echo -e "   1. Sign up at https://huggingface.co (free)"
    echo -e "   2. Go to Settings → Access Tokens"
    echo -e "   3. Create New Token → Select 'Read' permissions"
    echo -e "   4. Copy token and add to .env file"
    echo -e ""
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if NVIDIA Docker runtime is available
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  NVIDIA Docker runtime not available. GPU acceleration will be disabled.${NC}"
    echo -e "${YELLOW}⚠️  The container will still work but AI inference will be slower.${NC}"
fi

# Create data directories
echo -e "${GREEN}📁 Creating data directories...${NC}"
mkdir -p data/projects data/vector_db data/embeddings

# Build the Docker image
echo -e "${GREEN}Building JustCopy AI IDE Docker image...${NC}"
docker build -t local-coding-agent . || {
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo -e "${GREEN}🎉 You can now run the container with:${NC}"
echo -e "${BLUE}   docker-compose up${NC}"
echo -e "${BLUE}   or${NC}"
echo -e "${BLUE}   ./run.sh${NC}"
