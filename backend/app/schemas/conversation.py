from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    is_image_generation: bool = False
    is_web_search: bool = False

class MessageResponse(MessageBase):
    id: int
    role: str
    conversation_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True 