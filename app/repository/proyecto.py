from sqlalchemy.orm import Session
from sqlalchemy import text

class ProyectoRepository:
    
    def listar(self, db: Session):
        """Obtiene todos los proyectos activos del catálogo"""
        # Asumiendo que tienes un SP para listar o usas una consulta directa
        query_text = "SELECT id, nombre, descripcion FROM dbo.proyecto WHERE is_active = 1"
        return db.execute(text(query_text)).mappings().all()
    
    def asignar_proyecto(self, db: Session, empresa_id: int, proyecto_id: int):
        """Asigna un proyecto a una empresa"""
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_EmpresaProyecto
                    @Accion = 'Asignar',
                    @empresa_id = :empresa_id,
                    @proyecto_id = :proyecto_id
            """),
            {"empresa_id": empresa_id, "proyecto_id": proyecto_id}
        )