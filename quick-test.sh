#!/bin/bash

# Quick test script for Kimi K2 AI IDE
# This script performs basic functionality tests

echo "🧪 Quick Test - Kimi K2 AI IDE"
echo "=============================="

# Test 1: Check if container is running
echo "1. Checking container status..."
if docker ps | grep -q kimi-k2-ide; then
    echo "   ✅ Container is running"
else
    echo "   ❌ Container is not running"
    echo "   💡 Run './run.sh' to start the container"
    exit 1
fi

# Test 2: Check main interface
echo "2. Testing main interface..."
if curl -s http://localhost:8888/health > /dev/null; then
    echo "   ✅ Main interface is accessible"
else
    echo "   ❌ Main interface is not accessible"
fi

# Test 3: Check VS Code Server
echo "3. Testing VS Code Server..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "   ✅ VS Code Server is accessible"
else
    echo "   ❌ VS Code Server is not accessible"
fi

# Test 4: Check vLLM API
echo "4. Testing vLLM API..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ vLLM API is accessible"
else
    echo "   ❌ vLLM API is not accessible"
fi

# Test 5: Quick AI test
echo "5. Testing AI functionality..."
response=$(curl -s -X POST "http://localhost:8888/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Say hello"}]}' \
    --max-time 30)

if echo "$response" | grep -q "choices"; then
    echo "   ✅ AI is responding"
else
    echo "   ❌ AI is not responding properly"
    echo "   💡 This might take a few minutes after startup"
fi

echo ""
echo "🎉 Quick test completed!"
echo "🔗 Access your IDE at: http://localhost:8888"
echo "💻 VS Code IDE: http://localhost:8080"
echo ""
echo "📊 For detailed logs: docker logs kimi-k2-ide"
echo "🛑 To stop: docker stop kimi-k2-ide"
