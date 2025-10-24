# app/repository/documento_onedrive.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Any

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
        """
        Crea un nuevo documento en la BD.
        Paso 1: Ejecuta la creación y obtiene el ID.
        Paso 2: Obtiene el documento completo con ese ID.
        """
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
        
        # Paso 1: Obtener el ID que retornó el SP
        doc_id_map = result.mappings().first()
        if not doc_id_map or 'id' not in doc_id_map:
             # Maneja el caso en que el SP no devuelva el ID
             raise Exception("El Stored Procedure 'Crear' no devolvió el ID del nuevo documento.")
        
        # NO HAY DB.COMMIT() AQUÍ

        # Paso 2: Devolver el documento recién creado usando el ID
        # Esto funciona porque está dentro de la misma transacción de sesión (db)
        return self.obtener_por_id(db, doc_id_map['id'])

    def obtener_por_id(self, db: Session, documento_id: int):
        """Obtiene un documento por ID"""
        return db.execute(
            text("EXEC dbo.sp_CRUD_Documentos @Accion='Obtener', @id=:id"),
            {'id': documento_id}
        ).mappings().first()
    
    def listar(
        self, 
        db: Session, 
        tipo_documento: Optional[str] = None,
        estado: Optional[str] = None, 
        empresa_id: Optional[int] = None
    ) -> List[Any]:
        """
        Lista documentos con filtros opcionales.
        Devuelve los resultados mapeados por nombre de columna.
        """
        resultado = db.execute(
            text("""
                EXEC dbo.sp_CRUD_Documentos 
                    @Accion='Listar',
                    @tipo_documento=:tipo,
                    @estado=:estado,
                    @empresa_id=:empresa
            """),
            {
                "tipo": tipo_documento,
                "estado": estado, 
                "empresa": empresa_id
            }
        )
        # Convierte TODOS los resultados en una lista de "mappings" (dict-like)
        return resultado.mappings().all()

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
        # No db.commit()
    
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
        # No db.commit()
    
    def eliminar(self, db: Session, documento_id: int):
        """Elimina lógicamente un documento (estado=anulado)"""
        db.execute(
            text("EXEC dbo.sp_CRUD_Documentos @Accion='Eliminar', @id=:id"),
            {'id': documento_id}
        )
        # No db.commit()
    
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
        # No db.commit()
    
    def obtener_historial(self, db: Session, documento_id: int):
        """Obtiene el historial completo de un documento"""
        return db.execute(
            text("EXEC dbo.sp_ObtenerHistorial @documento_id=:documento_id"),
            {'documento_id': documento_id}
        ).mappings().all()