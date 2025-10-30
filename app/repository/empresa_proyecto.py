from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

class EmpresaProyectoRepository:
    
    def _convert_row_to_dict(self, row) -> Dict[str, Any]:
        """Convierte una fila de SQLAlchemy RowMapping a un diccionario simple."""
        return dict(row)

    def asignar(self, db: Session, empresa_id: int, proyecto_id: int) -> None:
        """
        Ejecuta el SP para asignar un proyecto a una empresa.
        No hace commit.
        """
        db.execute(
            text("EXEC sp_CRUD_EmpresaProyecto @Accion = :accion, @empresa_id = :empresa_id, @proyecto_id = :proyecto_id"),
            {'accion': 'Asignar', 'empresa_id': empresa_id, 'proyecto_id': proyecto_id}
        )
        # No commit here (manejado por el servicio)

    def desasignar(self, db: Session, empresa_id: int, proyecto_id: int) -> None:
        """
        Ejecuta el SP para desasignar un proyecto de una empresa.
        No hace commit.
        """
        db.execute(
            text("EXEC sp_CRUD_EmpresaProyecto @Accion = :accion, @empresa_id = :empresa_id, @proyecto_id = :proyecto_id"),
            {'accion': 'Desasignar', 'empresa_id': empresa_id, 'proyecto_id': proyecto_id}
        )
        # No commit here (manejado por el servicio)

    def listar_por_empresa(self, db: Session, empresa_id: int) -> List[Dict[str, Any]]:
        """
        Ejecuta el SP para listar los proyectos de una empresa y devuelve una lista de diccionarios.
        """
        result = db.execute(
            text("EXEC sp_CRUD_EmpresaProyecto @Accion = :accion, @empresa_id = :empresa_id"),
            {'accion': 'ListarProyectosPorEmpresa', 'empresa_id': empresa_id}
        ).mappings().all()
        
        # Convertir la lista de resultados (RowMappings) en una lista de diccionarios
        return [self._convert_row_to_dict(row) for row in result]

# Instancia única del repositorio para ser importada por el servicio
empresa_proyecto_repository = EmpresaProyectoRepository()
