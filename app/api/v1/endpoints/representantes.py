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
    """
    Obtiene todos los representantes (Lectura, no necesita commit).
    """
    return repo.get_all(db)

@router.get("/{id}", response_model=RepresentanteDetalles)
def get_representante_by_id(id: int, db: Session = Depends(get_db)):
    """
    Obtiene un representante por ID (Lectura, no necesita commit).
    """
    representante = repo.get_by_id(db, id)
    if not representante:
        raise HTTPException(status_code=404, detail="Representante no encontrado")
    return representante

@router.post("/", response_model=RepresentanteBase, status_code=status.HTTP_201_CREATED)
def create_representante(representante: RepresentanteCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo representante.
    """
    try:
        nuevo_representante = repo.create(db, representante)
        db.commit()
        db.refresh(nuevo_representante) 
        return nuevo_representante
    except Exception as e:
        db.rollback()
        # Verificar si es error de CUI duplicado
        if "cui" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un representante con el CUI {representante.cui}"
            )
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/{id}")
def update_representante(id: int, representante: RepresentanteUpdate, db: Session = Depends(get_db)):
    """
    Actualiza un representante.
    """
    try:
        # Primero verifica que existe
        if not repo.get_by_id(db, id):
             raise HTTPException(status_code=404, detail="Representante no encontrado")
        
        repo.update(db, id, representante)
        db.commit()  # <-- AÑADIDO
        return {"message": "Representante actualizado exitosamente"}
    except Exception as e:
        db.rollback() # <-- AÑADIDO
        raise e

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_representante(id: int, db: Session = Depends(get_db)):
    """
    Elimina (lógicamente) un representante.
    """
    try:
        # Primero verifica que existe
        if not repo.get_by_id(db, id):
             raise HTTPException(status_code=404, detail="Representante no encontrado")
             
        repo.delete(db, id)
        db.commit()  # <-- AÑADIDO
    except Exception as e:
        db.rollback() # <-- AÑADIDO
        raise e