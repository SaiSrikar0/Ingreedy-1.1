from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Request model for the chat endpoint"""
    message: str

class ChatResponse(BaseModel):
    """Response model for the chat endpoint"""
    message: str
    recipes: List[Dict[str, Any]] = [] 