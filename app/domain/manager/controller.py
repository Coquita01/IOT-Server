from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.domain.manager import schemas
from app.domain.manager.services import ManagerService
from typing import List

# Configuración del Router para el dominio de Manager
router = APIRouter(prefix="/manager", tags=["Manager"])

# Instancia global del servicio de lógica de negocio para el Manager
service = ManagerService()



@router.patch(
    "/users/{user_id}/toggle", 
    response_model=schemas.UserResponse,
    summary="Alternar estado de usuario",
    description="Activa o desactiva a un usuario específico. Requiere un motivo para la auditoría."
)
async def toggle_user(
    user_id: int,
    status_data: schemas.UserToggleRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Endpoint para cambiar el estado de actividad de un usuario.
    
    Args:
        user_id (int): ID numérico del usuario a modificar.
        status_data (UserToggleRequest): Nuevo estado (bool) y motivo del cambio.
        db (AsyncSession): Sesión de base de datos inyectada.
        
    Returns:
        UserResponse: Datos actualizados del usuario.
    """
    return await service.toggle_user_status(db, user_id, status_data)

@router.post(
    "/services/link", 
    response_model=schemas.UserServiceResponse,
    summary="Vincular usuario a servicio",
    description="Establece una relación formal entre un usuario final y un servicio del ecosistema."
)
async def link_service(
    link_data: schemas.LinkUserServiceRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Endpoint para la asignación de servicios a usuarios.
    
    Args:
        link_data (LinkUserServiceRequest): IDs del usuario y del servicio a vincular.
        db (AsyncSession): Sesión de base de datos inyectada.
        
    Returns:
        UserServiceResponse: Confirmación de la vinculación con fecha de asignación.
    """
    return await service.link_user_to_service(db, link_data)

@router.get(
    "/devices", 
    response_model=List[schemas.DeviceResponse],
    summary="Listar dispositivos supervisados",
    description="Obtiene la lista de todos los dispositivos IoT registrados bajo la supervisión del gerente."
)
async def list_devices(db: AsyncSession = Depends(get_session)):
    """
    Endpoint para la supervisión global de hardware.
    
    Args:
        db (AsyncSession): Sesión de base de datos inyectada.
        
    Returns:
        List[DeviceResponse]: Colección de dispositivos con sus estados actuales.
    """
    return await service.get_all_devices(db)