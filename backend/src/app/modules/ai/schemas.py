from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.tasks.models import Priority


class AIStatus(BaseModel):
    enabled: bool
    available: bool
    model: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @field_validator("messages")
    @classmethod
    def last_is_user(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages[-1].role != "user":
            raise ValueError("the last message must come from the user")
        return messages


class GenerateTasksRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    count: int = Field(default=5, ge=1, le=10)


class TaskDraft(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Priority = Priority.medium


class GenerateTasksResponse(BaseModel):
    tasks: list[TaskDraft]


class DescriptionSuggestion(BaseModel):
    description: str
