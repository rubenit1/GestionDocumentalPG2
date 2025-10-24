from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.empresa import EmpresaCreate, EmpresaUpdate

class EmpresaRepository:

    def get_all(self, db: Session, proyecto_id: Optional[int] = None):
        return db.execute(
            text("EXEC dbo.sp_CRUD_Empresa @Accion='Listar', @proyecto_id=:proyecto_id"),
            {'proyecto_id': proyecto_id}
        ).mappings().all()

    def get_by_razon_social(self, db: Session, razon_social: str):
        return db.execute(
            text("EXEC dbo.sp_CRUD_Empresa @Accion='ObtenerPorNombre', @razon_social=:razon_social"),
            {'razon_social': razon_social}
        ).mappings().first()

    def get_by_id(self, db: Session, id: int):
        return db.execute(text("EXEC dbo.sp_CRUD_Empresa @Accion='Obtener', @id=:id"), {'id': id}).mappings().first()

    def create(self, db: Session, empresa: EmpresaCreate):
        # 1. Ejecutamos el SP para insertar y obtener el ID
        result = db.execute(
            text("""
                EXEC dbo.sp_CRUD_Empresa @Accion='Crear', @razon_social=:razon_social,
                @autorizada_en=:autorizada_en, @fecha_autorizacion=:fecha_autorizacion,
                @autorizada_por=:autorizada_por, @inscrita_en=:inscrita_en,
                @numero_registro=:numero_registro, @numero_folio=:numero_folio,
                @numero_libro=:numero_libro, @tipo_libro=:tipo_libro,
                @lugar_notificaciones=:lugar_notificaciones,
                @segundo_lugar_notificaciones=:segundo_lugar_notificaciones
            """),
            empresa.dict()
        )
        # 2. Obtenemos la fila con el nuevo ID
        new_id_row = result.mappings().first()
        
        # 3. NO HACEMOS COMMIT AQUÍ
        # db.commit() <--- ELIMINADO

        # 4. Usamos el ID para obtener el objeto completo y limpio
        new_id = new_id_row['id']
        created_empresa = self.get_by_id(db, new_id)

        # 5. Devolvemos el objeto recién creado
        return created_empresa

    def update(self, db: Session, id: int, empresa: EmpresaUpdate):
        params = empresa.dict(exclude_unset=True)
        params['id'] = id
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_Empresa @Accion='Actualizar', @id=:id,
                @razon_social=:razon_social, @autorizada_en=:autorizada_en,
                @fecha_autorizacion=:fecha_autorizacion, @autorizada_por=:autorizada_por,
                @inscrita_en=:inscrita_en, @numero_registro=:numero_registro,
                @numero_folio=:numero_folio, @numero_libro=:numero_libro,
                @tipo_libro=:tipo_libro, @lugar_notificaciones=:lugar_notificaciones,
                @segundo_lugar_notificaciones=:segundo_lugar_notificaciones
            """),
            params
        )
        # NO HACEMOS COMMIT AQUÍ
        # db.commit() <--- ELIMINADO

    def delete(self, db: Session, id: int):
        db.execute(text("EXEC dbo.sp_CRUD_Empresa @Accion='Eliminar', @id=:id"), {'id': id})
        # NO HACEMOS COMMIT AQUÍ
        # db.commit() <--- ELIMINADO

    # --- AÑADE ESTE MÉTODO ---
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
        # NO HACEMOS COMMIT AQUÍ