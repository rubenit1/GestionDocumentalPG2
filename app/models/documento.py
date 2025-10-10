from pydantic import BaseModel, Field
from typing import Optional

class PersonaData(BaseModel):
    cui: Optional[str] = None
    nombre_completo: Optional[str] = Field(None, alias='nombreCompleto')
    direccion: Optional[str] = None
    edad: Optional[str] = None
    estado_civil: Optional[str] = Field(None, alias='estadoCivil')
    nacionalidad: Optional[str] = None
    profesion: Optional[str] = None
    posicion: Optional[str] = None
    class Config:
        populate_by_name = True

class ContratoData(BaseModel):
    tipo_contrato: Optional[str] = Field(None, alias='tipoContrato')
    fecha_inicio: Optional[str] = Field(None, alias='fechaInicio')
    fecha_fin: Optional[str] = Field(None, alias='fechaFin')
    monto: Optional[str] = None
    monto_en_letras: Optional[str] = Field(None, alias='montoEnLetras')
    descripcion_adicional: Optional[str] = Field(None, alias='descripcionAdicional')
    class Config:
        populate_by_name = True

class DocumentoProcesado(BaseModel):
    empresa_contratante: Optional[str] = Field(None, alias='empresaContratante')
    datos_persona: PersonaData = Field(..., alias='datosPersona')
    datos_contrato: ContratoData = Field(..., alias='datosContrato')
    class Config:
        populate_by_name = True

class GenerationRequest(BaseModel):
    template_name: str = Field(..., alias='templateName')
    fecha_contrato: str = Field(..., alias='fechaContrato')
    empresa_id: int = Field(..., alias='empresaId')
    representante_id: int = Field(..., alias='representanteId')
    colaborador_data: DocumentoProcesado = Field(..., alias='colaboradorData')
    class Config:
        populate_by_name = True