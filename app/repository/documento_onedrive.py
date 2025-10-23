# app/repository/documento_onedrive.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

class DocumentoOneDriveRepository:
    
    def crear(
        self, 
        db: Session,
        onedrive_file_id: str,
        onedrive_path: str,
        onedrive_web_url: Optional[str],
        nombre_archivo: str,
        tipo_documento: str,
        estado: str,
        usuario_creador_id: int,
        hash_sha256: str,
        tamano_bytes: Optional[int],
        empresa_id: Optional[int] = None,
        representante_id: Optional[int] = None,
        plantilla_id: Optional[int] = None,
        persona_id: Optional[int] = None,
        datos_ocr: Optional[str] = None,
        contenido_indexado: Optional[str] = None,
        tags: Optional[str] = None,
        categoria: Optional[str] = None,
        notas: Optional[str] = None
    ):
        """Crea un nuevo documento en la BD"""
        result = db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='Crear',
                    @onedrive_file_id=:onedrive_file_id,
                    @onedrive_path=:onedrive_path,
                    @onedrive_web_url=:onedrive_web_url,
                    @nombre_archivo=:nombre_archivo,
                    @tipo_documento=:tipo_documento,
                    @estado=:estado,
                    @usuario_creador_id=:usuario_creador_id,
                    @hash_sha256=:hash_sha256,
                    @tamano_bytes=:tamano_bytes,
                    @empresa_id=:empresa_id,
                    @representante_id=:representante_id,
                    @plantilla_id=:plantilla_id,
                    @persona_id=:persona_id,
                    @datos_ocr=:datos_ocr,
                    @contenido_indexado=:contenido_indexado,
                    @tags=:tags,
                    @categoria=:categoria,
                    @notas=:notas
            """),
            {
                'onedrive_file_id': onedrive_file_id,
                'onedrive_path': onedrive_path,
                'onedrive_web_url': onedrive_web_url,
                'nombre_archivo': nombre_archivo,
                'tipo_documento': tipo_documento,
                'estado': estado,
                'usuario_creador_id': usuario_creador_id,
                'hash_sha256': hash_sha256,
                'tamano_bytes': tamano_bytes,
                'empresa_id': empresa_id,
                'representante_id': representante_id,
                'plantilla_id': plantilla_id,
                'persona_id': persona_id,
                'datos_ocr': datos_ocr,
                'contenido_indexado': contenido_indexado,
                'tags': tags,
                'categoria': categoria,
                'notas': notas
            }
        )
        doc_id = result.mappings().first()
        db.commit()
        return self.obtener_por_id(db, doc_id['id'])
    
    def listar(
        self, 
        db: Session, 
        tipo_documento: Optional[str] = None,
        estado: Optional[str] = None,
        empresa_id: Optional[int] = None
    ):
        """Lista documentos con filtros opcionales"""
        return db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='Listar',
                    @tipo_documento=:tipo_documento,
                    @estado=:estado,
                    @empresa_id=:empresa_id
            """),
            {
                'tipo_documento': tipo_documento,
                'estado': estado,
                'empresa_id': empresa_id
            }
        ).mappings().all()
    
    def obtener_por_id(self, db: Session, documento_id: int):
        """Obtiene un documento por ID"""
        return db.execute(
            text("EXEC dbo.sp_CRUD_Documentos @Accion='Obtener', @id=:id"),
            {'id': documento_id}
        ).mappings().first()
    
    def buscar_por_contenido(self, db: Session, query: str):
        """Busca documentos por contenido o nombre"""
        return db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='BuscarPorContenido',
                    @contenido_indexado=:query
            """),
            {'query': query}
        ).mappings().all()
    
    def actualizar_estado(self, db: Session, documento_id: int, nuevo_estado: str):
        """Actualiza el estado de un documento"""
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='ActualizarEstado',
                    @id=:id,
                    @estado=:estado
            """),
            {'id': documento_id, 'estado': nuevo_estado}
        )
        db.commit()
    
    def actualizar(
        self,
        db: Session,
        documento_id: int,
        nombre_archivo: Optional[str] = None,
        estado: Optional[str] = None,
        empresa_id: Optional[int] = None,
        representante_id: Optional[int] = None,
        notas: Optional[str] = None
    ):
        """Actualiza un documento"""
        db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='Actualizar',
                    @id=:id,
                    @nombre_archivo=:nombre_archivo,
                    @estado=:estado,
                    @empresa_id=:empresa_id,
                    @representante_id=:representante_id,
                    @notas=:notas
            """),
            {
                'id': documento_id,
                'nombre_archivo': nombre_archivo,
                'estado': estado,
                'empresa_id': empresa_id,
                'representante_id': representante_id,
                'notas': notas
            }
        )
        db.commit()
    
    def eliminar(self, db: Session, documento_id: int):
        """Elimina lógicamente un documento (estado=anulado)"""
        db.execute(
            text("EXEC dbo.sp_CRUD_Documentos @Accion='Eliminar', @id=:id"),
            {'id': documento_id}
        )
        db.commit()
    
    def registrar_historial(
        self,
        db: Session,
        documento_id: int,
        accion: str,
        usuario_id: int,
        campo_modificado: Optional[str] = None,
        valor_anterior: Optional[str] = None,
        valor_nuevo: Optional[str] = None,
        notas: Optional[str] = None
    ):
        """Registra una acción en el historial del documento"""
        db.execute(
            text("""
                EXEC dbo.sp_RegistrarHistorial
                    @documento_id=:documento_id,
                    @accion=:accion,
                    @usuario_id=:usuario_id,
                    @campo_modificado=:campo_modificado,
                    @valor_anterior=:valor_anterior,
                    @valor_nuevo=:valor_nuevo,
                    @notas=:notas
            """),
            {
                'documento_id': documento_id,
                'accion': accion,
                'usuario_id': usuario_id,
                'campo_modificado': campo_modificado,
                'valor_anterior': valor_anterior,
                'valor_nuevo': valor_nuevo,
                'notas': notas
            }
        )
        db.commit()
    
    def obtener_historial(self, db: Session, documento_id: int):
        """Obtiene el historial completo de un documento"""
        return db.execute(
            text("EXEC dbo.sp_ObtenerHistorial @documento_id=:documento_id"),
            {'documento_id': documento_id}
        ).mappings().all()