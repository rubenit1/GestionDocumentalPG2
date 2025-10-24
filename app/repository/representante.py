from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.representante import RepresentanteCreate, RepresentanteUpdate

class RepresentanteRepository:
    def get_all(self, db: Session):
        # ... (esta función se mantiene igual)
        return db.execute(text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Listar'")).mappings().all()

    def get_by_id(self, db: Session, id: int):
        # ... (esta función se mantiene igual)
        return db.execute(text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Obtener', @id=:id"), {'id': id}).mappings().first()

    def create(self, db: Session, representante: RepresentanteCreate):
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

        
        new_id = new_id_row['id']
        created_representante = self.get_by_id(db, new_id)
        
        return created_representante

    def update(self, db: Session, id: int, representante: RepresentanteUpdate):
        # ... (esta función se mantiene igual)
        params = representante.dict(exclude_unset=True)
        params['id'] = id
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Actualizar', @id=:id,
                @nombre_completo=:nombre_completo, @fecha_nacimiento=:fecha_nacimiento,
                @estado_civil=:estado_civil, @profesion=:profesion,
                @nacionalidad=:nacionalidad, @cui=:cui,
                @extendido_en=:extendido_en, @genero_id=:genero_id
            """),
            params
        )


    def delete(self, db: Session, id: int):
        # ... (esta función se mantiene igual)
        db.execute(text("EXEC dbo.sp_CRUD_RepresentanteLegal @Accion='Eliminar', @id=:id"), {'id': id})
