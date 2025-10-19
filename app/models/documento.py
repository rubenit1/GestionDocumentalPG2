# app/models/documento.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class PersonaData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    cui: Optional[str] = None
    nombre_completo: Optional[str] = Field(None, serialization_alias='nombre_completo')
    direccion: Optional[str] = None
    edad: Optional[str] = None
    estado_civil: Optional[str] = Field(None, serialization_alias='estado_civil')
    nacionalidad: Optional[str] = None
    profesion: Optional[str] = None
    posicion: Optional[str] = None

class ContratoData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    tipo_contrato: Optional[str] = Field(None, serialization_alias='tipo_contrato')
    fecha_inicio: Optional[str] = Field(None, serialization_alias='fecha_inicio')
    fecha_fin: Optional[str] = Field(None, serialization_alias='fecha_fin')
    monto: Optional[str] = None
    monto_en_letras: Optional[str] = Field(None, serialization_alias='monto_en_letras')
    descripcion_adicional: Optional[str] = Field(None, serialization_alias='descripcion_adicional')

class DocumentoProcesado(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    empresa_contratante: Optional[str] = Field(None, serialization_alias='empresa_contratante')
    datos_persona: PersonaData = Field(..., serialization_alias='datos_persona')
    datos_contrato: ContratoData = Field(..., serialization_alias='datos_contrato')

class GenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    template_name: str = Field(..., alias='templateName')
    fecha_contrato: str = Field(..., alias='fechaContrato')
    empresa_id: int = Field(..., alias='empresaId')
    representante_id: int = Field(..., alias='representanteId')
    colaborador_data: DocumentoProcesado = Field(..., alias='colaboradorData')