# app/models/empresa_representante.py
from pydantic import BaseModel

class EmpresaRepresentanteBase(BaseModel):
    empresa_id: int
    representante_id: int

class EmpresaRepresentanteCreate(EmpresaRepresentanteBase):
    pass