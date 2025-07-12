#!/usr/bin/env python3
"""
AI Server using transformers library for real model inference
"""
import os
import json
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Local AI Server", version="1.0.0")

# Global variables for model and tokenizer
model = None
tokenizer = None
generator = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "local-model"
    messages: List[ChatMessage]
    max_tokens: int = 1000
    temperature: float = 0.7

class ChatResponse(BaseModel):
    choices: List[Dict[str, Any]]

def load_model():
    """Load the AI model and tokenizer"""
    global model, tokenizer, generator
    
    try:
        model_name = os.getenv("MODEL_NAME", "microsoft/DialoGPT-medium")
        # Use a coding-focused model if available
        if "Kimi" in model_name:
            model_name = "microsoft/CodeGPT-small-py"  # Fallback to a coding model
        logger.info(f"Loading model: {model_name}")
        
        # Check if we have a GPU available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add pad token if it doesn't exist
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with appropriate settings
        if device == "cuda":
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                trust_remote_code=True
            )
            model = model.to(device)
        
        # Create text generation pipeline
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if device == "cuda" else -1,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        
        logger.info("Model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False

# Initialize model on startup
def initialize_model():
    """Initialize the model"""
    success = load_model()
    if not success:
        logger.warning("Model loading failed, but server will continue with fallback responses")

# Load model when module is imported
initialize_model()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """Chat completions endpoint compatible with OpenAI API"""
    try:
        if not generator:
            # Fallback response if model isn't loaded
            return ChatResponse(choices=[{
                "message": {
                    "role": "assistant",
                    "content": "AI model is not loaded. Please check the server logs and ensure you have the required dependencies installed."
                }
            }])
        
        # Extract the last user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        prompt = user_messages[-1].content
        
        # Generate response
        response = generator(
            prompt,
            max_length=len(prompt.split()) + request.max_tokens,
            temperature=request.temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            num_return_sequences=1,
            truncation=True
        )
        
        # Extract generated text (remove the original prompt)
        generated_text = response[0]['generated_text']
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return ChatResponse(choices=[{
            "message": {
                "role": "assistant",
                "content": generated_text or "I'm here to help with your coding tasks!"
            }
        }])
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "data": [{
            "id": "local-model",
            "object": "model",
            "owned_by": "local",
            "permission": []
        }]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
