"""
Pydantic Schemas for Authentication and User Management
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= Authentication Schemas =============

class UserRegister(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # minutes


class TokenData(BaseModel):
    """Schema for decoded token data"""
    username: Optional[str] = None
    user_id: Optional[int] = None


# ============= User Schemas =============

class UserResponse(BaseModel):
    """Schema for user information (without sensitive data)"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Dataset Schemas =============

class DatasetInfo(BaseModel):
    """Schema for dataset information"""
    id: str
    name: str
    rows: int
    columns: int
    columns_info: List[Dict[str, Any]]
    created_at: datetime
    owner_id: int
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str
    dataset_id: str
    history: Optional[List[Dict[str, str]]] = []

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 characters)')
        return v.strip()


class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str
    chart_spec: Optional[Dict[str, Any]] = None
    data: Optional[List[Dict[str, Any]]] = None
