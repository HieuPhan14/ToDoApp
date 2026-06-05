from pydantic import BaseModel, Field, ConfigDict, EmailStr
from models.task import TaskStatus
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(max_length=300)
    due_date: datetime | None = None
    status: TaskStatus = TaskStatus.pending

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, max_length=300)
    due_date: datetime | None = None
    status: TaskStatus | None = None

class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(min_length=1, max_length=100)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=30)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

class Token(BaseModel):
    access_token: str 
    token_type: str 

