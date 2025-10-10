from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.empresa import EmpresaBase, EmpresaDetalles, EmpresaCreate, EmpresaUpdate
from app.models.representante import RepresentanteBase
from app.models.empresa_representante import EmpresaRepresentanteCreate
from app.repository.empresa_representante import EmpresaRepresentanteRepository
from app.services.empresa import EmpresaService # <-- Importante

router = APIRouter()
# Instanciamos los servicios y repositorios una sola vez
empresa_service = EmpresaService() 
empresa_rep_repo = EmpresaRepresentanteRepository()

@router.get("/", response_model=List[EmpresaBase])
def get_all_empresas(db: Session = Depends(get_db)):
    return empresa_service.get_all_empresas(db)

@router.get("/{id}", response_model=EmpresaDetalles)
def get_empresa_by_id(id: int, db: Session = Depends(get_db)):
    # La validación de 404 ahora está en el servicio
    return empresa_service.get_empresa_by_id(db, id)

@router.post("/", response_model=EmpresaBase, status_code=status.HTTP_201_CREATED)
def create_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    # La validación de duplicados ahora está en el servicio
    return empresa_service.create_empresa(db, empresa)

@router.put("/{id}")
def update_empresa(id: int, empresa: EmpresaUpdate, db: Session = Depends(get_db)):
    return empresa_service.update_empresa(db, id, empresa)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_empresa(id: int, db: Session = Depends(get_db)):
    empresa_service.delete_empresa(db, id)

# --- ENDPOINTS PARA LA RELACIÓN EMPRESA-REPRESENTANTE ---

@router.get("/{empresa_id}/representantes", response_model=List[RepresentanteBase])
def get_representantes_de_empresa(empresa_id: int, db: Session = Depends(get_db)):
    return empresa_rep_repo.listar_por_empresa(db, empresa_id)

@router.post("/representantes/asignar", status_code=status.HTTP_204_NO_CONTENT)
def asignar_representante_a_empresa(asignacion: EmpresaRepresentanteCreate, db: Session = Depends(get_db)):
    empresa_rep_repo.asignar(db, asignacion)
    return

@router.delete("/representantes/desasignar", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_representante_de_empresa(asignacion: EmpresaRepresentanteCreate, db: Session = Depends(get_db)):
    empresa_rep_repo.desasignar(db, asignacion)
    return