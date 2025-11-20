from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.empresa import EmpresaBase, EmpresaDetalles, EmpresaCreate, EmpresaUpdate
from app.models.representante import RepresentanteBase
from app.models.empresa import EmpresaPublic
from app.models.empresa_representante import EmpresaRepresentanteCreate
from app.repository.empresa_representante import EmpresaRepresentanteRepository
from app.services.empresa import EmpresaService

router = APIRouter()
# Instanciamos los servicios y repositorios una sola vez
empresa_service = EmpresaService() 
empresa_rep_repo = EmpresaRepresentanteRepository()

@router.get("/", response_model=List[EmpresaPublic])
def get_all_empresas(
    db: Session = Depends(get_db), 
    proyecto_id: Optional[int] = None
):
    """
    Obtiene todas las empresas, filtrando opcionalmente por proyecto_id.
    """
    return empresa_service.get_all_empresas(db, proyecto_id=proyecto_id)

@router.get("/{id}", response_model=EmpresaDetalles)
def get_empresa_by_id(id: int, db: Session = Depends(get_db)):
    """
    Obtiene una empresa por ID.
    La validación de 404 está en el servicio.
    """
    return empresa_service.get_empresa_by_id(db, id)

@router.post("/", response_model=EmpresaBase, status_code=status.HTTP_201_CREATED)
def create_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva empresa.
    El commit se hace al final, después de que el servicio funcione.
    """
    try:
        nueva_empresa = empresa_service.create_empresa(db, empresa)
        db.commit() # <-- CORRECCIÓN: El commit va DESPUÉS de la operación
        db.refresh(nueva_empresa) # Opcional: refresca el objeto con datos de la BD
        return nueva_empresa
    except Exception as e:
        db.rollback() # <-- Deshace la operación si algo falla
        raise e

@router.put("/{id}")
def update_empresa(id: int, empresa: EmpresaUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una empresa existente.
    """
    try:
        resultado = empresa_service.update_empresa(db, id, empresa)
        db.commit() # <-- AÑADIDO: Faltaba el commit
        return resultado
    except Exception as e:
        db.rollback()
        raise e
    
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_empresa(id: int, db: Session = Depends(get_db)):
    """
    Elimina (lógicamente) una empresa.
    """
    try:
        empresa_service.delete_empresa(db, id)
        db.commit() # <-- Correcto
    except Exception as e:
        db.rollback()
        raise e

# --- ENDPOINTS PARA LA RELACIÓN EMPRESA-REPRESENTANTE ---

@router.get("/{empresa_id}/representantes", response_model=List[RepresentanteBase])
def get_representantes_de_empresa(empresa_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los representantes asignados a una empresa.
    """
    return empresa_rep_repo.listar_por_empresa(db, empresa_id)

@router.post("/representantes/asignar", status_code=status.HTTP_204_NO_CONTENT)
def asignar_representante_a_empresa(asignacion: EmpresaRepresentanteCreate, db: Session = Depends(get_db)):
    """
    Asigna un representante a una empresa.
    """
    try:
        empresa_rep_repo.asignar(db, asignacion)
        db.commit() # <-- AÑADIDO: Faltaba el commit
        return
    except Exception as e:
        db.rollback()
        raise e

@router.delete("/representantes/desasignar", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_representante_de_empresa(asignacion: EmpresaRepresentanteCreate, db: Session = Depends(get_db)):
    """
    Desasigna un representante de una empresa.
    """
    try:
        empresa_rep_repo.desasignar(db, asignacion)
        db.commit() # <-- AÑADIDO: Faltaba el commit
        return
    except Exception as e:
        db.rollback()
        raise e

@router.post("/{empresa_id}/proyectos/{proyecto_id}", status_code=204)
def asignar_proyecto_a_empresa(
    empresa_id: int,
    proyecto_id: int,
    db: Session = Depends(get_db)
):
    """
    Asigna un proyecto existente a una empresa existente.
    """
    try:
        empresa_service.asignar_proyecto(db, empresa_id, proyecto_id) 
        db.commit() # <-- Correcto
        return None
    except Exception as e:
        db.rollback()
        raise e
    
    