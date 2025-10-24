from pydantic import BaseModel
from typing import Optional

class ProyectoBase(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True