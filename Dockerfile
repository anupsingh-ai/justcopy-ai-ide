# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=all

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    curl \
    wget \
    nodejs \
    npm \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install VS Code Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Copy VS Code extensions list
COPY vscode-extensions.txt /tmp/vscode-extensions.txt

# Install VS Code extensions
RUN while read extension; do \
    if [[ ! "$extension" =~ ^#.* ]] && [[ -n "$extension" ]]; then \
        code-server --install-extension "$extension" || true; \
    fi; \
    done < /tmp/vscode-extensions.txt

# Copy application files
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data/vector_db /app/data/projects /app/data/embeddings

# Download and cache embedding model
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Expose ports
# 8000: vLLM API
# 8080: VS Code Server
# 8888: Main application API
EXPOSE 8000 8080 8888

# Create startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Set the entrypoint
ENTRYPOINT ["/app/start.sh"]
