"""Centralized authentication service"""
from app.shared.auth.repository import AuthRepository
from app.shared.middleware.auth.devices.auth import CryptoManager
from app.shared.middleware.auth.human.human import HumanCryptoManager
from app.shared.auth.schemas import LoginRequest
from app.database.model import Device, User
from app.domain.device.schemas import PuzzleRequest as DevicePuzzleRequest
from app.shared.middleware.auth.human.puzzle import PuzzleRequest as HumanPuzzleRequest
from app.shared.session.service import SessionService
from sqlmodel import Session

class AuthService:
    def __init__(self):
        self.repo = AuthRepository()

    async def login(self, data: LoginRequest, request):
        session: Session = request.state.db
        session_service = SessionService(session)
        entity = data.entity.lower()
        if entity == "device":
            puzzle = DevicePuzzleRequest(**data.payload)
            manager = CryptoManager(session, session_service)
            return await manager.authenticate(puzzle, request_info={"ip": request.client.host})
        elif entity in ("user", "admin", "administrator", "manager", "master"):
            puzzle = HumanPuzzleRequest(**data.payload)
            manager = HumanCryptoManager(session, session_service)
            return await manager.authenticate(puzzle, request_info={"ip": request.client.host}, entity=entity)
        else:
            return {"valid": False, "error": "Unsupported entity"}
