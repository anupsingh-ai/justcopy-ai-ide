#!/usr/bin/env python3
"""
Test script to verify the Kimi K2 IDE setup
"""
import requests
import json
import time
import sys

def test_service(url, name, timeout=5):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: {str(e)}")
        return False

def test_ai_chat():
    """Test AI chat functionality"""
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello! Can you help me with Python programming?"}
            ]
        }
        
        response = requests.post(
            "http://localhost:8888/api/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print("✅ AI Chat: Working")
                print(f"   Response: {data['choices'][0]['message']['content'][:100]}...")
                return True
        
        print(f"❌ AI Chat: Failed - {response.text}")
        return False
        
    except Exception as e:
        print(f"❌ AI Chat: {str(e)}")
        return False

def test_code_generation():
    """Test code generation functionality"""
    try:
        payload = {
            "prompt": "Create a simple Python function to add two numbers",
            "context": "I need a basic function for arithmetic operations"
        }
        
        response = requests.post(
            "http://localhost:8888/api/code/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "code" in data:
                print("✅ Code Generation: Working")
                print(f"   Generated: {data['code'][:100]}...")
                return True
        
        print(f"❌ Code Generation: Failed - {response.text}")
        return False
        
    except Exception as e:
        print(f"❌ Code Generation: {str(e)}")
        return False

def test_project_creation():
    """Test project creation functionality"""
    try:
        payload = {
            "name": "test-project",
            "description": "A test project",
            "template": "python"
        }
        
        response = requests.post(
            "http://localhost:8888/api/projects/create",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Project Creation: Working")
            return True
        else:
            print(f"❌ Project Creation: Failed - {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Project Creation: {str(e)}")
        return False

def main():
    print("🧪 Testing Kimi K2 AI IDE Services")
    print("=" * 40)
    
    # Test basic services
    services = [
        ("http://localhost:8888/health", "Main API"),
        ("http://localhost:8080", "VS Code Server"),
        ("http://localhost:8000/health", "vLLM API")
    ]
    
    all_passed = True
    
    for url, name in services:
        if not test_service(url, name):
            all_passed = False
    
    print("\n🤖 Testing AI Functionality")
    print("-" * 30)
    
    # Test AI functionality (only if main API is working)
    if test_service("http://localhost:8888/health", "Main API", timeout=1):
        if not test_ai_chat():
            all_passed = False
        
        if not test_code_generation():
            all_passed = False
        
        if not test_project_creation():
            all_passed = False
    else:
        print("⏭️  Skipping AI tests - Main API not available")
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Your Kimi K2 IDE is ready to use.")
        print("\n🔗 Access your IDE at:")
        print("   Main Interface: http://localhost:8888")
        print("   VS Code: http://localhost:8080")
    else:
        print("❌ Some tests failed. Check the logs and try again.")
        print("\n📊 View logs with: docker logs kimi-k2-ide")
        sys.exit(1)

if __name__ == "__main__":
    main()
