from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class NodeCreate(BaseModel):
    name: str
    host: str
    port: int = Field(ge=1, le=65535)

    @field_validator('host')
    @classmethod
    def host_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('host must not be empty')
        return v

class NodeUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)

class NodeResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
