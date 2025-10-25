# app/repository/representante.py
from typing import Optional, List, Any # Importa List y Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.representante import RepresentanteCreate, RepresentanteUpdate

class RepresentanteRepository:
    def get_all(self, db: Session) -> List[Any]: # Especifica el tipo de retorno
        # Usar .mappings().all() sigue siendo la forma preferida para listas
        return db.execute(text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Listar'")).mappings().all()

    def get_by_id(self, db: Session, id: int) -> Optional[dict]: # Cambiado el tipo de retorno a dict
        result_mapping = db.execute(
            text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Obtener', @id=:id"),
            {'id': id}
        ).mappings().first()

        # Convertir explícitamente a dict si no es None
        return dict(result_mapping) if result_mapping else None

    def create(self, db: Session, representante: RepresentanteCreate) -> Optional[dict]: # Cambiado el tipo de retorno
        result = db.execute(
            text("""
                EXEC dbo.sp_CRUD_RepresentanteLegal
                    @Accion='Crear', @nombre_completo=:nombre_completo,
                    @fecha_nacimiento=:fecha_nacimiento, @cui=:cui, @genero_id=:genero_id,
                    @estado_civil=:estado_civil, @profesion=:profesion,
                    @nacionalidad=:nacionalidad, @extendido_en=:extendido_en
            """),
            representante.dict()
        )
        new_id_row = result.mappings().first()

        if not new_id_row or 'id' not in new_id_row:
             # Considera loguear este error también
             raise Exception("El Stored Procedure 'Crear' no devolvió el ID del nuevo representante.")

        new_id = new_id_row['id']
        # Llamamos a get_by_id que ahora devuelve un dict
        created_representante_dict = self.get_by_id(db, new_id)

        # NO HAY COMMIT AQUÍ (Correcto)

        return created_representante_dict # Devolvemos el dict

    def update(self, db: Session, id: int, representante: RepresentanteUpdate):
        # Prepara los parámetros, excluyendo los no enviados por el frontend
        params = representante.dict(exclude_unset=True)
        params['id'] = id # Añade el ID para el WHERE

        # Ejecuta el SP
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Actualizar', @id=:id,
                @nombre_completo=:nombre_completo, @fecha_nacimiento=:fecha_nacimiento,
                @estado_civil=:estado_civil, @profesion=:profesion,
                @nacionalidad=:nacionalidad, @cui=:cui,
                @extendido_en=:extendido_en, @genero_id=:genero_id
            """),
            # Pasa todos los posibles parámetros, ISNULL en el SP maneja los que no vengan
            {
                'id': params.get('id'),
                'nombre_completo': params.get('nombre_completo'),
                'fecha_nacimiento': params.get('fecha_nacimiento'),
                'estado_civil': params.get('estado_civil'),
                'profesion': params.get('profesion'),
                'nacionalidad': params.get('nacionalidad'),
                'cui': params.get('cui'),
                'extendido_en': params.get('extendido_en'),
                'genero_id': params.get('genero_id')
            }
        )
        # NO HAY COMMIT AQUÍ (Correcto)

    def delete(self, db: Session, id: int):
        # Ejecuta el SP
        db.execute(text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Eliminar', @id=:id"), {'id': id})
        # NO HAY COMMIT AQUÍ (Correcto)