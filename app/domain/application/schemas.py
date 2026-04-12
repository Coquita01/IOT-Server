from pydantic import BaseModel
from app.shared.base_domain.schemas import BaseSchemaResponse
from uuid import UUID


class ApplicationCreate(BaseModel):
    name: str
    version: str | None = None 
    url: str | None = None 
    port: int | None = None
    description: str | None = None
    administrator_id: UUID
    


class ApplicationUpdate(BaseModel):
    name: str | None = None 
    version: str | None = None 
    url: str | None = None 
    port: int | None = None 
    description: str | None = None
    is_active: bool | None = None 
    
    


class ApplicationResponse(BaseSchemaResponse):
    name: str
    version: str | None
    url: str | None
    port: int | None
    description: str | None
    administrator_id: UUID
    api_key: str
    is_active: bool 

class PuzzlePayload(BaseModel):
    ciphertext: str
    iv: str


class PuzzleRequest(BaseModel):
    application_id: UUID
    encrypted_payload: PuzzlePayload