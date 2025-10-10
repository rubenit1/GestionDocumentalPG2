# app/models/plantilla.py
from pydantic import BaseModel
from typing import Optional

class PlantillaSchema(BaseModel):
    id: int
    nombre: str
    descripcion: str
    nombre_archivo: str
    categoria: str
    campos_requeridos: Optional[str] = None

    class Config:
        from_attributes = True