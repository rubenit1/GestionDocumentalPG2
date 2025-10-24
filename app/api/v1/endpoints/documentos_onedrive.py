# app/api/v1/endpoints/documentos_onedrive.py
"""
Endpoint para gestión de documentos con integración OneDrive
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import json

from app.db.session import get_db
from app.services.onedrive_service import OneDriveService
from app.repository.documento_onedrive import DocumentoOneDriveRepository
from app.models.documento_onedrive import (
    DocumentoBase, 
    DocumentoDetalle, 
    DocumentoUpdate,
    HistorialDocumento
)

router = APIRouter()
onedrive_service = OneDriveService()
documento_repo = DocumentoOneDriveRepository()

# Usuario ID temporal (debe venir de autenticación JWT)
USUARIO_ACTUAL_ID = 1


@router.post("/upload", response_model=DocumentoDetalle)
async def subir_documento(
    file: UploadFile = File(...),
    tipo_documento: str = Form(...),
    categoria: str = Form(...),
    empresa_id: Optional[int] = Form(None),
    representante_id: Optional[int] = Form(None),
    notas: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Sube un documento a OneDrive y registra en BD
    """
    try:
        # ... (Tu lógica de leer archivo, hash, y subir a OneDrive) ...
        file_content = await file.read()
        file_hash = onedrive_service.calcular_hash(file_content)
        rutas = {
            "contrato": "/Documentos_Legales/Contratos",
            "minuta": "/Documentos_Legales/Minutas",
            "anexo": "/Documentos_Legales/Anexos",
            "carta": "/Documentos_Legales/Cartas"
        }
        base_path = rutas.get(tipo_documento, "/Documentos_Legales/Otros")
        onedrive_path = f"{base_path}/{file.filename}"
        
        resultado_upload = onedrive_service.subir_archivo(
            file_path=file.filename,
            onedrive_path=onedrive_path,
            file_content=file_content
        )
        
        file_id = resultado_upload["id"]
        web_url = onedrive_service.obtener_link_compartido(file_id, tipo="view")
        
        print(f"✅ Archivo subido. ID: {file_id}")
        
        # Registrar en base de datos
        documento = documento_repo.crear(
            db=db,
            onedrive_file_id=file_id,
            onedrive_path=onedrive_path,
            onedrive_web_url=web_url,
            nombre_archivo=file.filename,
            tipo_documento=tipo_documento,
            estado="borrador",
            usuario_creador_id=USUARIO_ACTUAL_ID,
            hash_sha256=file_hash,
            tamano_bytes=len(file_content),
            empresa_id=empresa_id,
            representante_id=representante_id,
            categoria=categoria,
            notas=notas
        )
        
        # Registrar en historial
        documento_repo.registrar_historial(
            db=db,
            documento_id=documento['id'],
            accion="creado",
            usuario_id=USUARIO_ACTUAL_ID,
            notas=f"Documento subido a OneDrive: {onedrive_path}"
        )
        
        # --- AÑADIDO ---
        db.commit()
        db.refresh(documento) # Refresca el objeto
        
        return documento
        
    except Exception as e:
        # --- AÑADIDO ---
        db.rollback() 
        print(f"❌ Error subiendo documento: {str(e)}")
        # ... (Manejo de borrado de archivo en OneDrive si falla la BD podría ir aquí)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DocumentoBase])
def listar_documentos(
    tipo_documento: Optional[str] = None,
    estado: Optional[str] = None,
    empresa_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista documentos con filtros opcionales"""
    # (Este es un GET, no necesita commit)
    return documento_repo.listar(
        db=db,
        tipo_documento=tipo_documento,
        estado=estado,
        empresa_id=empresa_id
    )


@router.get("/{documento_id}", response_model=DocumentoDetalle)
def obtener_documento(documento_id: int, db: Session = Depends(get_db)):
    """Obtiene detalles de un documento"""
    # (Este es un GET, no necesita commit)
    documento = documento_repo.obtener_por_id(db, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return documento


@router.get("/{documento_id}/download")
def descargar_documento(documento_id: int, db: Session = Depends(get_db)):
    """Descarga un documento desde OneDrive"""
    # (Este es un GET, no necesita commit)
    documento = documento_repo.obtener_por_id(db, documento_id)
    # ... (resto de tu lógica de descarga) ...
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        file_content = onedrive_service.descargar_archivo(documento['onedrive_file_id'])
        current_hash = onedrive_service.calcular_hash(file_content)
        if current_hash != documento['hash_sha256']:
            print(f"⚠️ ADVERTENCIA: Hash no coincide para documento {documento_id}")
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={documento['nombre_archivo']}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando: {str(e)}")


@router.put("/{documento_id}", response_model=DocumentoDetalle)
def actualizar_documento(
    documento_id: int,
    actualizacion: DocumentoUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza información de un documento"""
    try:
        documento_anterior = documento_repo.obtener_por_id(db, documento_id)
        if not documento_anterior:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Actualizar en BD
        documento_repo.actualizar(
            db=db,
            documento_id=documento_id,
            nombre_archivo=actualizacion.nombre_archivo,
            estado=actualizacion.estado,
            empresa_id=actualizacion.empresa_id,
            representante_id=actualizacion.representante_id,
            notas=actualizacion.notas
        )
        
        # Registrar cambios en historial
        if actualizacion.estado and actualizacion.estado != documento_anterior['estado']:
            documento_repo.registrar_historial(
                db=db,
                documento_id=documento_id,
                accion="actualizado",
                usuario_id=USUARIO_ACTUAL_ID,
                campo_modificado="estado",
                valor_anterior=documento_anterior['estado'],
                valor_nuevo=actualizacion.estado
            )
        
        # --- AÑADIDO ---
        db.commit()
        
        return documento_repo.obtener_por_id(db, documento_id)
        
    except Exception as e:
        # --- AÑADIDO ---
        db.rollback()
        raise e


@router.delete("/{documento_id}")
def eliminar_documento(documento_id: int, db: Session = Depends(get_db)):
    """Elimina lógicamente un documento (no lo borra de OneDrive)"""
    try:
        documento = documento_repo.obtener_por_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        documento_repo.eliminar(db, documento_id)
        
        documento_repo.registrar_historial(
            db=db,
            documento_id=documento_id,
            accion="eliminado",
            usuario_id=USUARIO_ACTUAL_ID,
            notas="Documento marcado como anulado"
        )
        
        # --- AÑADIDO ---
        db.commit()
        
        return {"message": "Documento eliminado exitosamente"}

    except Exception as e:
        # --- AÑADIDO ---
        db.rollback()
        raise e


@router.post("/{documento_id}/cambiar-estado")
def cambiar_estado(
    documento_id: int,
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Cambia el estado de un documento
    """
    try:
        estados_validos = ["borrador", "revision", "aprobado", "firmado", "archivado", "anulado"]
        if nuevo_estado not in estados_validos:
            raise HTTPException(status_code=400, detail=f"Estado inválido. Use: {estados_validos}")
        
        documento_anterior = documento_repo.obtener_por_id(db, documento_id)
        if not documento_anterior:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        documento_repo.actualizar_estado(db, documento_id, nuevo_estado)
        
        documento_repo.registrar_historial(
            db=db,
            documento_id=documento_id,
            accion="cambio_estado",
            usuario_id=USUARIO_ACTUAL_ID,
            campo_modificado="estado",
            valor_anterior=documento_anterior['estado'],
            valor_nuevo=nuevo_estado
        )
        
        # --- AÑADIDO ---
        db.commit()
        
        return {"message": f"Estado actualizado a: {nuevo_estado}"}

    except Exception as e:
        # --- AÑADIDO ---
        db.rollback()
        raise e


# ... (El resto de tus endpoints GET no necesitan cambios) ...

@router.get("/{documento_id}/historial", response_model=List[HistorialDocumento])
def obtener_historial(documento_id: int, db: Session = Depends(get_db)):
    documento = documento_repo.obtener_por_id(db, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return documento_repo.obtener_historial(db, documento_id)

@router.get("/buscar/{query}")
def buscar_documentos(query: str, db: Session = Depends(get_db)):
    return documento_repo.buscar_por_contenido(db, query)

@router.get("/{documento_id}/link-onedrive")
def obtener_link_onedrive(documento_id: int, db: Session = Depends(get_db)):
    documento = documento_repo.obtener_por_id(db, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {
        "onedrive_url": documento['onedrive_web_url'],
        "nombre_archivo": documento['nombre_archivo']
    }