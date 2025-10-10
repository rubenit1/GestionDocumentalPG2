# app/models/representante.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

class RepresentanteBase(BaseModel):
    id: int
    nombre_completo: str
    cui: str

class RepresentanteDetalles(RepresentanteBase):
    fecha_nacimiento: date
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    extendido_en: Optional[str] = None
    genero_id: int
    is_active: bool

class RepresentanteCreate(BaseModel):
    nombre_completo: str
    fecha_nacimiento: date
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    cui: str
    extendido_en: Optional[str] = None
    genero_id: int

class RepresentanteUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    nacionalidad: Optional[str] = None
    cui: Optional[str] = None
    extendido_en: Optional[str] = None
    genero_id: Optional[int] = None