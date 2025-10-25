# app/api/v1/endpoints/representantes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional # Asegúrate de importar Optional
from sqlalchemy.exc import IntegrityError # Importar para manejo de duplicados

from app.db.session import get_db
from app.repository.representante import RepresentanteRepository
from app.models.representante import RepresentanteBase, RepresentanteDetalles, RepresentanteCreate, RepresentanteUpdate

router = APIRouter()
repo = RepresentanteRepository()

@router.get("/", response_model=List[RepresentanteBase])
def get_all_representantes(db: Session = Depends(get_db)):
    """
    Obtiene todos los representantes activos.
    """
    return repo.get_all(db)

@router.get("/{id}", response_model=RepresentanteDetalles)
def get_representante_by_id(id: int, db: Session = Depends(get_db)):
    """
    Obtiene un representante por su ID.
    """
    representante = repo.get_by_id(db, id)
    if not representante:
        raise HTTPException(status_code=404, detail="Representante no encontrado")
    # Pydantic/FastAPI convierten el dict devuelto por el repo al modelo RepresentanteDetalles
    # gracias a from_attributes=True en el modelo.
    return representante

@router.post("/", response_model=RepresentanteBase, status_code=status.HTTP_201_CREATED)
def create_representante(representante: RepresentanteCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo representante legal.
    """
    try:
        # repo.create ahora devuelve un dict o None
        nuevo_representante_dict = repo.create(db, representante)
        if not nuevo_representante_dict:
             # Esto no debería pasar si el SP devuelve ID, pero por si acaso
             raise HTTPException(status_code=500, detail="No se pudo obtener el representante creado después de la inserción.")

        db.commit() # Confirma la transacción

        # Devolvemos el dict directamente, FastAPI lo convierte al response_model RepresentanteBase
        # Si RepresentanteBase no tiene todos los campos de nuevo_representante_dict, Pydantic los filtrará.
        return nuevo_representante_dict

    except IntegrityError as e: # Capturar error de duplicado (si tienes UNIQUE constraint)
        db.rollback()
        # Puedes intentar extraer el nombre de la constraint si es más específico
        if "UQ_representante_cui" in str(e): # Ajusta "UQ_representante_cui" al nombre real de tu constraint
            detail = f"Ya existe un representante con el CUI {representante.cui}"
        else:
            detail = f"Error de integridad al crear representante: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
    except Exception as e:
        db.rollback()
        # Loguear el error real podría ser útil aquí para depuración
        print(f"Error inesperado al crear representante: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear el representante.")

@router.put("/{id}", response_model=RepresentanteDetalles) # Devuelve el objeto completo actualizado
def update_representante(id: int, representante: RepresentanteUpdate, db: Session = Depends(get_db)):
    """
    Actualiza un representante existente.
    """
    try:
        # Verifica si existe antes de actualizar
        representante_existente = repo.get_by_id(db, id)
        if not representante_existente:
             raise HTTPException(status_code=404, detail="Representante no encontrado")

        # Ejecuta la actualización en el repositorio
        repo.update(db, id, representante)
        db.commit() # Confirma la transacción

        # Obtiene y devuelve el representante actualizado
        representante_actualizado = repo.get_by_id(db, id)
        if not representante_actualizado:
             # Esto sería raro si el update fue exitoso, pero maneja el caso
             raise HTTPException(status_code=500, detail="No se pudo obtener el representante después de actualizar.")
        return representante_actualizado

    except IntegrityError as e: # Capturar error de duplicado si se actualiza CUI a uno existente
        db.rollback()
        if "UQ_representante_cui" in str(e):
             detail = f"Ya existe otro representante con el CUI proporcionado."
        else:
             detail = f"Error de integridad al actualizar representante: {str(e)}"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    except Exception as e:
        db.rollback()
        print(f"Error inesperado al actualizar representante: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al actualizar el representante.")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_representante(id: int, db: Session = Depends(get_db)):
    """
    Elimina (lógicamente) un representante marcándolo como inactivo.
    """
    try:
        # Verifica si existe antes de eliminar
        if not repo.get_by_id(db, id):
             raise HTTPException(status_code=404, detail="Representante no encontrado")

        # Ejecuta la eliminación lógica en el repositorio
        repo.delete(db, id)
        db.commit() # Confirma la transacción

        # No se devuelve cuerpo en respuestas 204 No Content
        return None
    except Exception as e:
        db.rollback()
        print(f"Error inesperado al eliminar representante: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al eliminar el representante.")