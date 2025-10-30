# app/models/empresa.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


# --- MODELO NUEVO/CORREGIDO PARA LA LISTA ---
# Este es el modelo que tu endpoint GET /empresas/ debe usar
class EmpresaPublic(BaseModel):
    id: int
    razon_social: str
    lugar_notificaciones: Optional[str] = None
    numero_registro: Optional[str] = None  # El frontend lo usa como CIF

    # --- CAMPOS FALTANTES ---
    proyecto_id: Optional[int] = None
    proyecto_nombre: Optional[str] = None

    class Config:
        from_attributes = True  # Para Pydantic v2 (era orm_mode)
# --- FIN DEL MODELO PARA LA LISTA ---


class EmpresaBase(BaseModel):
    id: int
    razon_social: str
    lugar_notificaciones: Optional[str] = None


class EmpresaDetalles(EmpresaBase):
    autorizada_en: Optional[str] = None
    fecha_autorizacion: Optional[date] = None
    autorizada_por: Optional[str] = None
    inscrita_en: Optional[str] = None
    numero_registro: Optional[str] = None
    numero_folio: Optional[str] = None
    numero_libro: Optional[str] = None
    tipo_libro: Optional[str] = None
    segundo_lugar_notificaciones: Optional[str] = None
    is_active: bool


class EmpresaCreate(BaseModel):
    razon_social: str
    proyecto_id: Optional[int] = None
    representante_ids: Optional[List[int]] = None
    autorizada_en: Optional[str] = None
    fecha_autorizacion: Optional[date] = None
    autorizada_por: Optional[str] = None
    inscrita_en: Optional[str] = None
    numero_registro: Optional[str] = None
    numero_folio: Optional[str] = None
    numero_libro: Optional[str] = None
    tipo_libro: Optional[str] = None
    lugar_notificaciones: Optional[str] = None
    segundo_lugar_notificaciones: Optional[str] = None


class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = None
    autorizada_en: Optional[str] = None
    fecha_autorizacion: Optional[date] = None
    autorizada_por: Optional[str] = None
    inscrita_en: Optional[str] = None
    numero_registro: Optional[str] = None
    numero_folio: Optional[str] = None
    numero_libro: Optional[str] = None
    tipo_libro: Optional[str] = None
    lugar_notificaciones: Optional[str] = None
    segundo_lugar_notificaciones: Optional[str] = None
