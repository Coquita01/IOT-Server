from pydantic import BaseModel
from uuid import UUID

# --- PuzzlePayload and PuzzleRequest for puzzle-type authentication ---
class PuzzlePayload(BaseModel):
    ciphertext: str
    iv: str

class PuzzleRequest(BaseModel):
    device_id: UUID
    encrypted_payload: PuzzlePayload
from app.domain.personal_data.schemas import NonCriticalPersonalDataResponse


class AdministratorResponse(NonCriticalPersonalDataResponse):
    pass
