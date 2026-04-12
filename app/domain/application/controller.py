from fastapi import HTTPException, status, Request
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.application.schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate, PuzzleRequest
from app.domain.application.service import ApplicationServiceDep
from app.database import SessionDep
from app.shared.middleware.auth.applications.auth import CryptoManager
from app.shared.session.service import SessionService
from app.config import settings


class ApplicationController(FullCrudApiController):
    prefix = "/applications"
    tags = ["Applications"]
    service_dep = ApplicationServiceDep
    response_schema = ApplicationResponse
    create_schema = ApplicationCreate
    update_schema = ApplicationUpdate


application_router = ApplicationController().router


@application_router.post("/auth")
async def authenticate_application(
    puzzle: PuzzleRequest,
    session: SessionDep,
    request: Request,
):
    session_service = SessionService(
        valkey_url=settings.VALKEY_URL,
        encryption_key=settings.ENCRYPTION_KEY,
    )

    request_info = {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }

    crypto = CryptoManager(session, session_service)
    result = await crypto.authenticate(puzzle, request_info)

    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"],
        )

    return result