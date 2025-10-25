# app/models/representante.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

class RepresentanteBase(BaseModel):
    id: int
    nombre_completo: str
    cui: str

    # --- AÑADE ESTO ---
    class Config:
        from_attributes = True # O orm_mode = True si usas Pydantic v1

class RepresentanteDetalles(RepresentanteBase):
    fecha_nacimiento: date
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    extendido_en: Optional[str] = None
    genero_id: int
    is_active: bool

    # --- AÑADE ESTO (o asegúrate que ya lo hereda si RepresentanteBase lo tiene) ---
    # Si RepresentanteBase ya tiene Config, esta no es estrictamente necesaria
    # pero no hace daño tenerla explícitamente.
    class Config:
        from_attributes = True # O orm_mode = True si usas Pydantic v1

class RepresentanteCreate(BaseModel):
    # (Este modelo no necesita Config porque es para entrada (request body))
    nombre_completo: str
    fecha_nacimiento: date
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    cui: str
    extendido_en: Optional[str] = None
    genero_id: int

class RepresentanteUpdate(BaseModel):
    # (Este modelo no necesita Config porque es para entrada (request body))
    nombre_completo: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    cui: Optional[str] = None
    extendido_en: Optional[str] = None
    genero_id: Optional[int] = None