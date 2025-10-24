# app/repository/plantilla.py
from sqlalchemy.orm import Session
from sqlalchemy import text

class PlantillaRepository:
    def get_all(self, db: Session):
        result = db.execute(text("EXEC sp_Plantilla_ListarActivos"))
        return result.mappings().all()

    def create(self, db: Session, nombre: str, descripcion: str, nombre_archivo: str, categoria: str, campos_requeridos: str):
        params = {
            'nombre': nombre,
            'descripcion': descripcion,
            'nombre_archivo': nombre_archivo,
            'categoria': categoria,
            'campos_requeridos': campos_requeridos
        }
        db.execute(
            text("""
                EXEC sp_Plantilla_Crear 
                @nombre=:nombre, @descripcion=:descripcion, @nombre_archivo=:nombre_archivo,
                @categoria=:categoria, @campos_requeridos=:campos_requeridos
            """),
            params
        )
