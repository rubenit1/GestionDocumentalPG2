# app/api/v1/endpoints/flujo_completo.py
"""
Endpoint que integra el flujo completo:
1. OCR de imagen
2. Generación de documento
3. Subida a OneDrive
4. Registro en BD
"""

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import datetime

from app.db.session import get_db
from app.services.onedrive_service import OneDriveService
from app.services.documento_v2 import ServicioDocumentoV2
from app.services.ocr import parse_ocr_text
from app.repository.documento_onedrive import DocumentoOneDriveRepository
from app.models.documento import GenerationRequest, DocumentoProcesado

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import uuid

router = APIRouter()
onedrive_service = OneDriveService()
documento_service = ServicioDocumentoV2()
documento_repo = DocumentoOneDriveRepository()

USUARIO_ACTUAL_ID = 1


@router.post("/procesar-y-generar")
async def procesar_imagen_y_generar_contrato(
    # Imagen para OCR
    imagen: UploadFile = File(...),
    
    # Datos del contrato
    template_name: str = Form(...),
    fecha_contrato: str = Form(...),
    empresa_id: int = Form(...),
    representante_id: int = Form(...),
    
    # Categorización
    categoria: str = Form("contrato"),
    notas: Optional[str] = Form(None),
    
    db: Session = Depends(get_db)
):
    """
    Flujo completo:
    1. Recibe imagen con datos del colaborador
    2. Extrae datos con OCR
    3. Genera documento Word con plantilla
    4. Sube documento a OneDrive
    5. Registra en base de datos
    
    Retorna: Información del documento creado + link de OneDrive
    """
    
    try:
        print("\n" + "="*70)
        print("🚀 INICIANDO FLUJO COMPLETO")
        print("="*70)
        
        # ===== PASO 1: OCR DE LA IMAGEN =====
        print("\n📸 PASO 1: Procesando imagen con OCR...")
        
        contents = await imagen.read()
        image = Image.open(io.BytesIO(contents))
        
        # Preprocesamiento
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        brightness = ImageEnhance.Brightness(image)
        image = brightness.enhance(1.2)
        sharpener = ImageEnhance.Sharpness(image)
        image = sharpener.enhance(3.0)
        image = image.filter(ImageFilter.SHARPEN)
        
        # Extraer texto
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(image, lang='spa', config=custom_config)
        
        # Parsear datos
        datos_ocr = parse_ocr_text(extracted_text)
        
        print(f"✅ Datos extraídos: {datos_ocr['datos_persona']['nombre_completo']}")
        
        # ===== PASO 2: GUARDAR IMAGEN ORIGINAL EN ONEDRIVE =====
        print("\n📤 PASO 2: Guardando imagen original en OneDrive...")
        
        imagen_filename = f"OCR_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.filename}"
        imagen_path = f"/Documentos_Legales/Imagenes_Originales/{imagen_filename}"
        
        resultado_imagen = onedrive_service.subir_archivo(
            file_path=imagen_filename,
            onedrive_path=imagen_path,
            file_content=contents
        )
        
        print(f"✅ Imagen guardada: {resultado_imagen['id']}")
        
        # ===== PASO 3: GENERAR DOCUMENTO WORD =====
        print("\n📝 PASO 3: Generando documento Word...")
        
        # Crear objeto GenerationRequest
        colaborador_data = DocumentoProcesado(**datos_ocr)
        
        request = GenerationRequest(
            template_name=template_name,
            fecha_contrato=fecha_contrato,
            empresa_id=empresa_id,
            representante_id=representante_id,
            colaborador_data=colaborador_data
        )
        
        # Generar documento
        archivo_generado = documento_service.generar_documento(db, request)
        
        print(f"✅ Documento generado: {archivo_generado}")
        
        # ===== PASO 4: SUBIR DOCUMENTO A ONEDRIVE =====
        print("\n📤 PASO 4: Subiendo documento a OneDrive...")
        
        # Leer archivo generado
        with open(archivo_generado, 'rb') as f:
            doc_content = f.read()
        
        # Nombre descriptivo
        nombre_colaborador = datos_ocr['datos_persona']['nombre_completo'].replace(' ', '_')
        doc_filename = f"Contrato_{nombre_colaborador}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.docx"
        doc_path = f"/Documentos_Legales/Contratos/{doc_filename}"
        
        resultado_doc = onedrive_service.subir_archivo(
            file_path=doc_filename,
            onedrive_path=doc_path,
            file_content=doc_content
        )
        
        # Obtener link compartido
        doc_id = resultado_doc["id"]
        web_url = onedrive_service.obtener_link_compartido(doc_id, tipo="view")
        
        print(f"✅ Documento subido a OneDrive: {doc_id}")
        
        # ===== PASO 5: REGISTRAR EN BASE DE DATOS =====
        print("\n💾 PASO 5: Registrando en base de datos...")
        
        # Calcular hash
        doc_hash = onedrive_service.calcular_hash(doc_content)
        
        # Crear registro en BD
        documento = documento_repo.crear(
            db=db,
            onedrive_file_id=doc_id,
            onedrive_path=doc_path,
            onedrive_web_url=web_url,
            nombre_archivo=doc_filename,
            tipo_documento="contrato",
            estado="borrador",
            usuario_creador_id=USUARIO_ACTUAL_ID,
            hash_sha256=doc_hash,
            tamano_bytes=len(doc_content),
            empresa_id=empresa_id,
            representante_id=representante_id,
            datos_ocr=str(datos_ocr),  # Guardar JSON de datos OCR
            contenido_indexado=extracted_text,  # Para búsquedas
            categoria=categoria,
            notas=notas
        )
        
        # Registrar historial
        documento_repo.registrar_historial(
            db=db,
            documento_id=documento['id'],
            accion="creado",
            usuario_id=USUARIO_ACTUAL_ID,
            notas=f"Documento generado automáticamente desde OCR y subido a OneDrive"
        )
        
        print(f"✅ Registro creado en BD: ID {documento['id']}")
        
        # ===== LIMPIAR ARCHIVO LOCAL =====
        import os
        try:
            os.remove(archivo_generado)
            print(f"🗑️ Archivo local eliminado: {archivo_generado}")
        except:
            pass
        
        print("\n" + "="*70)
        print("✅ FLUJO COMPLETO FINALIZADO")
        print("="*70 + "\n")
        
        # ===== RETORNAR RESULTADO =====
        return {
            "success": True,
            "mensaje": "Documento procesado y guardado exitosamente",
            "documento": {
                "id": documento['id'],
                "nombre_archivo": doc_filename,
                "onedrive_url": web_url,
                "estado": "borrador",
                "tipo": "contrato"
            },
            "datos_extraidos": {
                "colaborador": datos_ocr['datos_persona']['nombre_completo'],
                "cui": datos_ocr['datos_persona']['cui'],
                "empresa": datos_ocr['empresa_contratante']
            },
            "imagen_original": {
                "onedrive_id": resultado_imagen['id'],
                "nombre": imagen_filename
            }
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN FLUJO COMPLETO: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el flujo: {str(e)}")


@router.get("/test-onedrive")
def test_onedrive():
    """Endpoint de prueba para verificar conexión con OneDrive"""
    try:
        token = onedrive_service._obtener_token()
        return {
            "status": "ok",
            "mensaje": "Conexión exitosa con OneDrive",
            "token_preview": token[:30] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a OneDrive: {str(e)}")