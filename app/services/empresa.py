from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repository.empresa import EmpresaRepository
from app.models.empresa import EmpresaCreate, EmpresaUpdate

class EmpresaService:
    def __init__(self):
        self.repository = EmpresaRepository()

    def get_all_empresas(self, db: Session):
        """ Obtiene todas las empresas. """
        return self.repository.get_all(db)

    def get_empresa_by_id(self, db: Session, id: int):
        """ Obtiene una empresa por ID, con validación. """
        empresa = self.repository.get_by_id(db, id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return empresa

    def create_empresa(self, db: Session, empresa: EmpresaCreate):
        """ Crea una nueva empresa, validando duplicados. """
        empresa_existente = self.repository.get_by_razon_social(db, empresa.razon_social)
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una empresa con la Razón Social '{empresa.razon_social}'."
            )
        return self.repository.create(db, empresa)
        
    def update_empresa(self, db: Session, id: int, empresa: EmpresaUpdate):
        """ Actualiza una empresa. """
        # Aquí podrías añadir lógica de negocio, como verificar que el nuevo nombre no exista ya.
        self.repository.update(db, id, empresa)
        return {"message": "Empresa actualizada exitosamente"}

    def delete_empresa(self, db: Session, id: int):
        """ Elimina (lógicamente) una empresa. """
        return self.repository.delete(db, id)