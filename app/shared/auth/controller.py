from fastapi import APIRouter, Request, status, HTTPException
from app.shared.auth.schemas import LoginRequest, LoginResponse
from app.shared.auth.service import AuthService

class AuthApiController:
    def __init__(self, entity: str, login_path: str, auth_service: AuthService = None):
        self.router = APIRouter()
        self.entity = entity
        self.auth_service = auth_service or AuthService()
        self._register_routes(login_path)

    def _register_routes(self, login_path):
        @self.router.post(login_path, response_model=LoginResponse, tags=["Login"])
        async def login(request: Request, data: LoginRequest):
            data.entity = self.entity
            result = await self.auth_service.login(data, request)
            if not result["valid"]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result["error"])
            return result
