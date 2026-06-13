from pydantic import BaseModel, EmailStr
from typing import Optional, List


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    username: Optional[str] = None
    bio: str = ""
    city: str = ""
    interests: Optional[List[str]] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    interests: Optional[List[str]] = None


class UserResponse(BaseModel):
    userId: str
    name: str
    email: EmailStr
    username: str
    bio: Optional[str] = None
    city: Optional[str] = None
    interests: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    class Config:
        from_attributes = True