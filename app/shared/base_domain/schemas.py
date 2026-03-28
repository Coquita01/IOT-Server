from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class BaseSchemaResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
