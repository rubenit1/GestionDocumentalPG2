from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.repository.proyecto import ProyectoRepository
from app.models.proyecto import ProyectoBase

router = APIRouter()
proyecto_repo = ProyectoRepository()

@router.get("/", response_model=List[ProyectoBase])
def listar_proyectos(
    db: Session = Depends(get_db)
):
    """Obtiene la lista de todos los proyectos (catálogo)"""
    return proyecto_repo.listar(db=db)