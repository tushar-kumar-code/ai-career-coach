from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessageItem(BaseModel):
    role: str = Field(description="'user' or 'assistant' / 'ai'")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(description="Current user prompt or question")
    history: Optional[List[ChatMessageItem]] = Field(default_factory=list, description="Recent conversation history")
    target_role: Optional[str] = Field(default=None, description="Optional target role override")


class ChatResponse(BaseModel):
    response: str = Field(description="AI Coach's response")
    provider: str = Field(description="Active AI Provider used")
    timestamp: Optional[str] = None
