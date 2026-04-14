from pydantic import BaseModel
from uuid import UUID

class PuzzlePayload(BaseModel):
    ciphertext: str
    iv: str

class PuzzleRequest(BaseModel):
    device_id: UUID
    encrypted_payload: PuzzlePayload
