from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from typing import List, Dict, Any
# Importamos el nuevo repositorio
from app.repository.empresa_proyecto import empresa_proyecto_repository

class EmpresaProyectoService:

    def __init__(self, repository=empresa_proyecto_repository):
        self.repository = repository

    def asignar(self, db: Session, empresa_id: int, proyecto_id: int) -> Dict[str, Any]:
        """Lógica de negocio para asignar un proyecto."""
        try:
            self.repository.asignar(db, empresa_id, proyecto_id)
            db.commit()
            return {"message": "Proyecto asignado correctamente"}
        except Exception as e:
            db.rollback()
            if "UNIQUE KEY" in str(e) or "PRIMARY KEY" in str(e):
                 raise HTTPException(status_code=409, detail="Esta asignación ya existe.")
            raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")

    def desasignar(self, db: Session, empresa_id: int, proyecto_id: int) -> Dict[str, Any]:
        """Lógica de negocio para desasignar un proyecto."""
        try:
            self.repository.desasignar(db, empresa_id, proyecto_id)
            db.commit()
            return {"message": "Proyecto desasignado correctamente"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")

    def listar_por_empresa(self, db: Session, empresa_id: int) -> List[Dict[str, Any]]:
        """Lógica de negocio para listar los proyectos de una empresa."""
        try:
            # El repositorio ya devuelve una lista de dicts
            return self.repository.listar_por_empresa(db, empresa_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")

# Instancia única del servicio para ser importada por los endpoints
empresa_proyecto_service = EmpresaProyectoService()

