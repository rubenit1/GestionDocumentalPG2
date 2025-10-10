from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.repository.representante import RepresentanteRepository
from app.models.representante import RepresentanteBase, RepresentanteDetalles, RepresentanteCreate, RepresentanteUpdate

router = APIRouter()
repo = RepresentanteRepository()

@router.get("/", response_model=List[RepresentanteBase])
def get_all_representantes(db: Session = Depends(get_db)):
    return repo.get_all(db)

@router.get("/{id}", response_model=RepresentanteDetalles)
def get_representante_by_id(id: int, db: Session = Depends(get_db)):
    representante = repo.get_by_id(db, id)
    if not representante:
        raise HTTPException(status_code=404, detail="Representante no encontrado")
    return representante

@router.post("/", response_model=RepresentanteBase, status_code=status.HTTP_201_CREATED)
def create_representante(representante: RepresentanteCreate, db: Session = Depends(get_db)):
    return repo.create(db, representante)

@router.put("/{id}")
def update_representante(id: int, representante: RepresentanteUpdate, db: Session = Depends(get_db)):
    repo.update(db, id, representante)
    return {"message": "Representante actualizado exitosamente"}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_representante(id: int, db: Session = Depends(get_db)):
    repo.delete(db, id)