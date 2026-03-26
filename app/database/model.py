from typing import Optional
from uuid import UUID
from app.shared.base_domain.model import BaseTable

class DatosPersonalesNoCriticos(BaseTable, table=True):
    __tablename__ = "datos_personales_no_criticos"

    nombre: str
    apellido_paterno: str
    apellido_materno: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    estado: str | None = None
    codigo_postal: str | None = None
    fecha_nacimiento: datetime | None = None
    activo: bool = Field(default=True)

    datos_sensibles: Optional["DatosSensibles"] = Relationship(
        back_populates="datos_no_criticos"
    )


class DatosSensibles(BaseTable, table=True):
    __tablename__ = "datos_sensibles"

    datos_no_criticos_id: UUID = Field(
        foreign_key="datos_personales_no_criticos.id", unique=True
    )
    email: str = Field(unique=True)
    password_hash: str
    curp: str | None = Field(default=None, unique=True)
    rfc: str | None = Field(default=None, unique=True)

    datos_no_criticos: DatosPersonalesNoCriticos = Relationship(
        back_populates="datos_sensibles"
    )
    administrador: Optional["Administrador"] = Relationship(
        back_populates="datos_sensibles"
    )
    gerente: Optional["Gerente"] = Relationship(back_populates="datos_sensibles")
    usuario: Optional["Usuario"] = Relationship(back_populates="datos_sensibles")


class Administrador(BaseTable, table=True):
    __tablename__ = "administrador"

    datos_sensibles_id: UUID = Field(foreign_key="datos_sensibles.id", unique=True)
    master: bool = Field(default=False)
    activo: bool = Field(default=True)

    datos_sensibles: DatosSensibles = Relationship(back_populates="administrador")
    servicios_registrados: list["Servicio"] = Relationship(
        back_populates="registrado_por"
    )
    aplicaciones_registradas: list["Aplicacion"] = Relationship(
        back_populates="registrada_por"
    )


class Gerente(BaseTable, table=True):
    __tablename__ = "gerente"

    datos_sensibles_id: UUID = Field(foreign_key="datos_sensibles.id", unique=True)
    activo: bool = Field(default=True)

    datos_sensibles: DatosSensibles = Relationship(back_populates="gerente")
    gerente_servicios: list["GerenteServicio"] = Relationship(back_populates="gerente")


class Usuario(BaseTable, table=True):
    __tablename__ = "usuario"

    datos_sensibles_id: UUID = Field(foreign_key="datos_sensibles.id", unique=True)
    activo: bool = Field(default=True)

    datos_sensibles: DatosSensibles = Relationship(back_populates="usuario")
    usuario_roles: list["UsuarioRol"] = Relationship(back_populates="usuario")


class Servicio(BaseTable, table=True):
    __tablename__ = "servicio"

    nombre: str = Field(unique=True)
    descripcion: str | None = None
    administrador_id: UUID = Field(foreign_key="administrador.id")
    activo: bool = Field(default=True)

    registrado_por: Administrador = Relationship(back_populates="servicios_registrados")
    gerente_servicios: list["GerenteServicio"] = Relationship(back_populates="servicio")
    aplicacion_servicios: list["AplicacionServicio"] = Relationship(
        back_populates="servicio"
    )
    dispositivo_servicios: list["DispositivoServicio"] = Relationship(
        back_populates="servicio"
    )
    roles: list["Rol"] = Relationship(back_populates="servicio")
    tickets_servicio: list["TicketServicio"] = Relationship(back_populates="servicio")


class GerenteServicio(BaseTable, table=True):
    __tablename__ = "gerente_servicio"

    gerente_id: UUID = Field(foreign_key="gerente.id")
    servicio_id: UUID = Field(foreign_key="servicio.id")

    gerente: Gerente = Relationship(back_populates="gerente_servicios")
    servicio: Servicio = Relationship(back_populates="gerente_servicios")
    tickets_ecosistema: list["TicketEcosistema"] = Relationship(
        back_populates="gerente_servicio"
    )


class Aplicacion(BaseTable, table=True):
    __tablename__ = "aplicacion"

    nombre: str
    version: str | None = None
    url: str | None = None
    descripcion: str | None = None
    administrador_id: UUID = Field(foreign_key="administrador.id")
    activo: bool = Field(default=True)

    registrada_por: Administrador = Relationship(
        back_populates="aplicaciones_registradas"
    )
    aplicacion_servicios: list["AplicacionServicio"] = Relationship(
        back_populates="aplicacion"
    )


class AplicacionServicio(BaseTable, table=True):
    __tablename__ = "aplicacion_servicio"

    aplicacion_id: UUID = Field(foreign_key="aplicacion.id")
    servicio_id: UUID = Field(foreign_key="servicio.id")

    aplicacion: Aplicacion = Relationship(back_populates="aplicacion_servicios")
    servicio: Servicio = Relationship(back_populates="aplicacion_servicios")


class Dispositivo(BaseTable, table=True):
    __tablename__ = "dispositivo"

    nombre: str
    marca: str | None = None
    modelo: str | None = None
    numero_serie: str | None = Field(default=None, unique=True)
    ip: str | None = None
    mac: str | None = Field(default=None, unique=True)
    activo: bool = Field(default=True)

    dispositivo_servicios: list["DispositivoServicio"] = Relationship(
        back_populates="dispositivo"
    )


class DispositivoServicio(BaseTable, table=True):
    __tablename__ = "dispositivo_servicio"

    dispositivo_id: UUID = Field(foreign_key="dispositivo.id")
    servicio_id: UUID = Field(foreign_key="servicio.id")

    dispositivo: Dispositivo = Relationship(back_populates="dispositivo_servicios")
    servicio: Servicio = Relationship(back_populates="dispositivo_servicios")


class Rol(BaseTable, table=True):
    __tablename__ = "rol"

    nombre: str
    descripcion: str | None = None
    servicio_id: UUID = Field(foreign_key="servicio.id")
    activo: bool = Field(default=True)

    servicio: Servicio = Relationship(back_populates="roles")
    permiso: Optional["PermisoRol"] = Relationship(back_populates="rol")
    usuario_roles: list["UsuarioRol"] = Relationship(back_populates="rol")


class PermisoRol(BaseTable, table=True):
    __tablename__ = "permiso_rol"

    rol_id: UUID = Field(foreign_key="rol.id", unique=True)
    puede_leer: bool = Field(default=False)
    puede_escribir: bool = Field(default=False)
    puede_eliminar: bool = Field(default=False)
    puede_administrar: bool = Field(default=False)

    rol: Rol = Relationship(back_populates="permiso")


class UsuarioRol(BaseTable, table=True):
    __tablename__ = "usuario_rol"

    usuario_id: UUID = Field(foreign_key="usuario.id")
    rol_id: UUID = Field(foreign_key="rol.id")

    usuario: Usuario = Relationship(back_populates="usuario_roles")
    rol: Rol = Relationship(back_populates="usuario_roles")
    tickets_servicio: list["TicketServicio"] = Relationship(
        back_populates="usuario_rol"
    )


class TicketStatus(SQLModel, table=True):
    __tablename__ = "ticket_status"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    descripcion: str | None = None

    tickets_servicio: list["TicketServicio"] = Relationship(back_populates="status")
    tickets_ecosistema: list["TicketEcosistema"] = Relationship(back_populates="status")


class TicketServicio(BaseTable, table=True):
    __tablename__ = "ticket_servicio"

    titulo: str
    descripcion: str | None = None
    usuario_rol_id: UUID = Field(foreign_key="usuario_rol.id")
    status_id: int = Field(foreign_key="ticket_status.id")
    servicio_id: UUID = Field(foreign_key="servicio.id")
    prioridad: str = Field(default="media")

    usuario_rol: UsuarioRol = Relationship(back_populates="tickets_servicio")
    status: TicketStatus = Relationship(back_populates="tickets_servicio")
    servicio: Servicio = Relationship(back_populates="tickets_servicio")


class TicketEcosistema(BaseTable, table=True):
    __tablename__ = "ticket_ecosistema"

    titulo: str
    descripcion: str | None = None
    gerente_servicio_id: UUID = Field(foreign_key="gerente_servicio.id")
    status_id: int = Field(foreign_key="ticket_status.id")
    prioridad: str = Field(default="media")

    gerente_servicio: GerenteServicio = Relationship(
        back_populates="tickets_ecosistema"
    )
    status: TicketStatus = Relationship(back_populates="tickets_ecosistema")
