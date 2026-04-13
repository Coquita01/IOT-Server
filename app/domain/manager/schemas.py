from pydantic import BaseModel
from uuid import UUID

# --- PuzzlePayload y PuzzleRequest para autenticación tipo puzzle ---
class PuzzlePayload(BaseModel):
    ciphertext: str
    iv: str

class PuzzleRequest(BaseModel):
    device_id: UUID
    encrypted_payload: PuzzlePayload
from app.domain.personal_data.schemas import NonCriticalPersonalDataResponse

class ManagerResponse(NonCriticalPersonalDataResponse):
    pass
