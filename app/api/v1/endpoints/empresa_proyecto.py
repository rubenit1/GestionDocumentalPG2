from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
# Se corrige la importación para que coincida con tu nombre de archivo (sin "_service")
from app.services.empresa_proyecto import empresa_proyecto_service
# Importamos el validador de roles que creamos en auth.py
from app.api.v1.endpoints.auth import require_roles
# Importamos los modelos de respuesta que usaremos
from app.models.usuario import TokenData # Asumiendo que require_roles lo necesita

# --- !! CORRECCIÓN AQUÍ !! ---
# Se quita el "prefix" de este router, porque ya se define en
# el archivo 'api.py' principal que lo incluye.
router = APIRouter(
    tags=["Empresa-Proyecto"],
    # Protegemos todas las rutas de este archivo para que requieran rol 'admin'
    dependencies=[Depends(require_roles(["admin"]))]
)
# --- Fin de la corrección ---


# --- Modelos Pydantic ---

class EmpresaProyectoPayload(BaseModel):
    """Modelo para el body de asignar y desasignar."""
    empresa_id: int
    proyecto_id: int
    # El SP requiere 'accion' pero lo manejamos a nivel de endpoint
    # accion: str # No es necesario en el payload del frontend

class ProyectoSimple(BaseModel):
    """Modelo de respuesta para un proyecto listado."""
    id: int
    nombre: str
    class Config:
        from_attributes = True # Pydantic v2 (era orm_mode)

# --- Endpoints ---

# Esta ruta ahora será POST /empresa-proyecto
@router.post("", status_code=201, summary="Asignar un proyecto a una empresa")
def asignar_proyecto_empresa(
    payload: EmpresaProyectoPayload, 
    db: Session = Depends(get_db)
):
    """
    Asigna un proyecto existente a una empresa existente.
    Body esperado: `{"empresa_id": 1, "proyecto_id": 2}`
    """
    return empresa_proyecto_service.asignar(db, payload.empresa_id, payload.proyecto_id)


# Esta ruta ahora será DELETE /empresa-proyecto
@router.delete("", status_code=200, summary="Desasignar un proyecto de una empresa")
def desasignar_proyecto_empresa(
    # DELETE con body no es estándar REST, pero coincide con el apiService
    payload: EmpresaProyectoPayload = Body(...), 
    db: Session = Depends(get_db)
):
    """
    Desasigna un proyecto de una empresa.
    Body esperado: `{"empresa_id": 1, "proyecto_id": 2}`
    """
    return empresa_proyecto_service.desasignar(db, payload.empresa_id, payload.proyecto_id)


# Esta ruta ahora será GET /empresa-proyecto/empresa/{empresa_id}
@router.get(
    "/empresa/{empresa_id}", 
    response_model=List[ProyectoSimple],
    summary="Listar los proyectos de una empresa"
)
def listar_proyectos_empresa(empresa_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los proyectos asociados a un ID de empresa específico.
    """
    return empresa_proyecto_service.listar_por_empresa(db, empresa_id)

