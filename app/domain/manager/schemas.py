"""
Schemas del Gerente — DTOs para requests y responses.

Este módulo define los modelos Pydantic utilizados como contratos de entrada
(requests) y salida (responses) para todos los endpoints del Gerente.

Secciones:
    - Usuarios:     Activación/desactivación y consulta de usuarios finales.
    - Servicios:    Consulta de servicios, vinculación y desvinculación de usuarios.
    - Dispositivos: Consulta de dispositivos, lecturas de sensores y reportes consolidados.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


# ─── Usuarios ────────────────────────────────────────────────


class UserToggleRequest(BaseModel):
    """
    Cuerpo de la petición para activar o desactivar un usuario final.

    Attributes:
        is_active (bool): Nuevo estado del usuario.
                          True = activo, False = inactivo.
    """
    is_active: bool


class UserResponse(BaseModel):
    """
    Respuesta estándar con los datos públicos de un usuario.

    Attributes:
        id (int):           Identificador único del usuario en la base de datos.
        nombre (str):       Nombre completo del usuario.
        email (str):        Correo electrónico del usuario.
        is_active (bool):   Estado actual del usuario (activo/inactivo).
        created_at (datetime): Fecha y hora de creación del registro.
    """
    id: int
    nombre: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Servicios ───────────────────────────────────────────────


class ServiceResponse(BaseModel):
    """
    Respuesta estándar con los datos de un servicio IoT.

    Attributes:
        id (int):                   Identificador único del servicio.
        nombre (str):               Nombre descriptivo del servicio.
        descripcion (Optional[str]): Descripción detallada del servicio. Puede ser nula.
        fecha_inicio (datetime):    Fecha y hora de inicio del servicio.
        fecha_fin (Optional[datetime]): Fecha y hora de finalización. Nula si el servicio
                                        está activo o no tiene fecha límite.
        estado (Optional[str]):     Estado actual del servicio (ej. 'activo', 'inactivo').
        gerente_id (Optional[int]): ID del gerente responsable del servicio. Puede ser nulo.
        created_at (datetime):      Fecha y hora de creación del registro.
    """
    id: int
    nombre: str
    descripcion: Optional[str] = None
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: Optional[str] = None
    gerente_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkUserServiceRequest(BaseModel):
    """
    Cuerpo de la petición para vincular un usuario a un servicio.

    El gerente utiliza este schema para asignar un usuario final
    a un servicio IoT específico bajo su gestión.

    Attributes:
        usuario_id (int):  ID del usuario a vincular.
        servicio_id (int): ID del servicio al que se vinculará el usuario.
    """
    usuario_id: int
    servicio_id: int

    model_config = {
        "json_schema_extra": {
            "example": {"usuario_id": 3, "servicio_id": 1}
        }
    }


class UnlinkUserServiceRequest(BaseModel):
    """
    Cuerpo de la petición para desvincular un usuario de un servicio.

    El gerente utiliza este schema para remover la relación entre
    un usuario final y un servicio IoT.

    Attributes:
        usuario_id (int):  ID del usuario a desvincular.
        servicio_id (int): ID del servicio del que se desvinculará el usuario.
    """
    usuario_id: int
    servicio_id: int

    model_config = {
        "json_schema_extra": {
            "example": {"usuario_id": 3, "servicio_id": 1}
        }
    }


class UserServiceResponse(BaseModel):
    """
    Respuesta que representa la relación entre un usuario y un servicio.

    Attributes:
        usuario_id (int):               ID del usuario vinculado.
        servicio_id (int):              ID del servicio al que está vinculado.
        gerente_id (Optional[int]):     ID del gerente que realizó la asignación. Puede ser nulo.
        fecha_asignacion (Optional[datetime]): Fecha y hora en que se realizó la vinculación.
    """
    usuario_id: int
    servicio_id: int
    gerente_id: Optional[int] = None
    fecha_asignacion: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Dispositivos ─────────────────────────────────────────────


class DeviceResponse(BaseModel):
    """
    Respuesta estándar con los datos de un dispositivo IoT.

    Attributes:
        id (int):               Identificador único del dispositivo.
        nombre (Optional[str]): Nombre o alias del dispositivo. Puede ser nulo.
        device_type (str):      Tipo de dispositivo (ej. 'sensor', 'actuador').
        is_active (bool):       Estado operativo del dispositivo (activo/inactivo).
        admin_id (Optional[int]): ID del administrador responsable del dispositivo.
        created_at (datetime):  Fecha y hora de registro del dispositivo.
    """
    id: int
    nombre: Optional[str] = None
    device_type: str
    is_active: bool
    admin_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SensorReadingResponse(BaseModel):
    """
    Respuesta que representa una lectura individual de un sensor.

    Attributes:
        id (int):           Identificador único de la lectura.
        device_id (int):    ID del dispositivo que generó la lectura.
        sensor_type (str):  Tipo de sensor (ej. 'temperatura', 'humedad', 'presión').
        value (float):      Valor numérico registrado por el sensor.
        unit (str):         Unidad de medida del valor (ej. '°C', '%', 'hPa').
        timestamp (datetime): Fecha y hora exacta en que se registró la lectura.
    """
    id: int
    device_id: int
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class DeviceReportResponse(BaseModel):
    """
    Reporte consolidado de un dispositivo con sus últimas lecturas de sensores.

    Agrupa la información del dispositivo junto con un historial reciente
    de lecturas y su estado de conectividad actual.

    Attributes:
        device (DeviceResponse):                Datos del dispositivo.
        last_readings (list[SensorReadingResponse]): Lista de las lecturas más recientes
                                                     registradas por el dispositivo.
        status (str): Estado de conectividad del dispositivo (ej. 'online', 'offline').
    """
    device: DeviceResponse
    last_readings: list[SensorReadingResponse]
    status: str

    model_config = {"from_attributes": True}