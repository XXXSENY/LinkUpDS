from pydantic import BaseModel
from typing import Optional, Dict, Any


class PostCreate(BaseModel):
    content: str
    topic: str = "general"


class PostResponse(BaseModel):
    postId: str
    content: str
    topic: str
    sentiment: Optional[str] = "neutral"
    sentimentScore: Optional[float] = 0.0
    likeCount: Optional[int] = 0
    author: Optional[Dict[str, Any]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    class Config:
        from_attributes = True