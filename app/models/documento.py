from pydantic import BaseModel, Field
from typing import Optional

class PersonaData(BaseModel):
    cui: Optional[str] = None
    nombre_completo: Optional[str] = None
    direccion: Optional[str] = None
    edad: Optional[str] = None
    estado_civil: Optional[str] = None
    nacionalidad: Optional[str] = None
    profesion: Optional[str] = None
    posicion: Optional[str] = None

class ContratoData(BaseModel):
    tipo_contrato: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    monto: Optional[str] = None
    monto_en_letras: Optional[str] = None
    descripcion_adicional: Optional[str] = None

class DocumentoProcesado(BaseModel):
    empresa_contratante: Optional[str] = Field(None, alias='empresaContratante')
    datos_persona: PersonaData = Field(..., alias='datosPersona')
    datos_contrato: ContratoData = Field(..., alias='datosContrato')

    class Config:
        populate_by_name = True
        orm_mode = True

class GenerationRequest(BaseModel):
    template_name: str = Field(..., alias='templateName')
    fecha_contrato: str = Field(..., alias='fechaContrato')
    empresa_id: int = Field(..., alias='empresaId')
    representante_id: int = Field(..., alias='representanteId')
    colaborador_data: DocumentoProcesado = Field(..., alias='colaboradorData')

    class Config:
        populate_by_name = True
        orm_mode = True
