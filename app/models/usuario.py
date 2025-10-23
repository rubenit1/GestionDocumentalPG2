# app/models/documento_onedrive.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentoCreate(BaseModel):
    nombre_archivo: str
    tipo_documento: str  # contrato, minuta, anexo, carta
    estado: str = "borrador"
    empresa_id: Optional[int] = None
    representante_id: Optional[int] = None
    plantilla_id: Optional[int] = None
    persona_id: Optional[int] = None
    categoria: Optional[str] = None
    notas: Optional[str] = None
    tags: Optional[str] = None  # JSON string

class DocumentoBase(BaseModel):
    id: int
    onedrive_file_id: str
    nombre_archivo: str
    tipo_documento: str
    estado: str
    fecha_creacion: datetime
    onedrive_web_url: Optional[str] = None

class DocumentoDetalle(DocumentoBase):
    onedrive_path: str
    hash_sha256: str
    tamano_bytes: Optional[int] = None
    version: int
    empresa_id: Optional[int] = None
    representante_id: Optional[int] = None
    usuario_creador_id: int
    fecha_modificacion: Optional[datetime] = None
    notas: Optional[str] = None
    tags: Optional[str] = None
    categoria: Optional[str] = None

class DocumentoUpdate(BaseModel):
    nombre_archivo: Optional[str] = None
    estado: Optional[str] = None
    empresa_id: Optional[int] = None
    representante_id: Optional[int] = None
    notas: Optional[str] = None

class HistorialDocumento(BaseModel):
    id: int
    accion: str
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    fecha_accion: datetime
    usuario_nombre: str
    notas: Optional[str] = None