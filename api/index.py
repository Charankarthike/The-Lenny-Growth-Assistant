"""
Vercel Serverless API for Lenny Growth Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="Lenny Growth Assistant API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None

@app.get("/")
async def root():
    return {"message": "Lenny Growth Assistant API", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Simple chat endpoint using OpenAI directly"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Convert messages
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Call OpenAI
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            sources=[]
        )
    except Exception as e:
        return ChatResponse(
            response=f"I'm having trouble connecting right now. Error: {str(e)}",
            sources=[]
        )

# Vercel serverless handler
handler = app
