from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# --- Modelos para el Frontend (lo que se envía/recibe) ---

class UserCreateRequest(BaseModel):
    """Modelo para crear un usuario (lo que envía el frontend)"""
    username: str
    email: EmailStr
    nombre: str  # El frontend envía 'nombre'
    password: str = Field(min_length=8)
    rol: str

class UserUpdateRequest(BaseModel):
    """Modelo para actualizar un usuario (lo que envía el frontend)"""
    username: str
    email: EmailStr
    nombre: str  # El frontend envía 'nombre'
    rol: str

class PasswordResetRequest(BaseModel):
    """Modelo para resetear password (lo que envía el frontend)"""
    user_id: int
    new_password: str = Field(min_length=8)


# --- Modelos para la Base de Datos (representación interna) ---

class UserInDB(BaseModel):
    """Modelo que representa al usuario como está en la BD"""
    id: int
    username: str
    email: EmailStr
    nombre_completo: str # La BD usa 'nombre_completo'
    rol: str
    is_active: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True # Permite mapear desde objetos SQL
        # Reemplazado por .from_orm() en Pydantic v2
        # Para Pydantic v2, se usaría from_attributes = True


# --- Modelos de Respuesta (lo que la API devuelve al frontend) ---

class UserPublic(BaseModel):
    """Modelo de usuario seguro para devolver al frontend"""
    id: int
    username: str
    email: EmailStr
    nombre: str # El frontend recibe 'nombre'
    rol: str
    is_active: bool
    fecha_creacion: Optional[datetime] = None

class TokenData(BaseModel):
    """Modelo para los datos dentro del JWT"""
    id: int
    username: str
    rol: str

class LoginResponse(BaseModel):
    """Modelo para la respuesta de /login"""
    ok: bool
    token: str
    user: UserPublic
