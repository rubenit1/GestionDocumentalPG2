# app/repository/empresa_representante.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.empresa_representante import EmpresaRepresentanteCreate

class EmpresaRepresentanteRepository:

    def asignar(self, db: Session, asignacion: EmpresaRepresentanteCreate):
        params = asignacion.dict()
        db.execute(
            text("EXEC dbo.sp_CRUD_EmpresaRepresentante @Accion='Asignar', @empresa_id=:empresa_id, @representante_id=:representante_id"),
            params
        )
        db.commit()

    def desasignar(self, db: Session, asignacion: EmpresaRepresentanteCreate):
        params = asignacion.dict()
        db.execute(
            text("EXEC dbo.sp_CRUD_EmpresaRepresentante @Accion='Desasignar', @empresa_id=:empresa_id, @representante_id=:representante_id"),
            params
        )
        db.commit()

    def listar_por_empresa(self, db: Session, empresa_id: int):
        return db.execute(
            text("EXEC dbo.sp_CRUD_EmpresaRepresentante @Accion='ListarPorEmpresa', @empresa_id=:empresa_id"),
            {'empresa_id': empresa_id}
        ).mappings().all()