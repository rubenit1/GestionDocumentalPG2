# app/api/v1/endpoints/documentos_v2.py
"""
Endpoint actualizado usando docxtpl para generación de documentos
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import pytesseract
from PIL import Image, ImageEnhance
import io

from app.db.session import get_db
from app.models.documento import DocumentoProcesado, GenerationRequest
from app.core.config import TESSERACT_CMD
from app.services.documento_v2 import ServicioDocumentoV2  # ← NUEVO SERVICIO

router = APIRouter()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
servicio_documento = ServicioDocumentoV2()  # ← INSTANCIA DEL NUEVO SERVICIO


@router.post("/ocr", response_model=DocumentoProcesado)
async def ocr_extract(file: UploadFile = File(...)):
    """
    Endpoint de OCR con preprocesamiento de imagen.
    Este endpoint NO cambia - sigue igual que antes
    """
    print(f"📄 Procesando imagen: {file.filename}")
    
    try:
        # Leer la imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Preprocesar imagen para mejorar OCR
        # 1. Convertir a escala de grises
        image = image.convert('L')
        
        # 2. Aumentar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # 3. Aumentar nitidez
        sharpener = ImageEnhance.Sharpness(image)
        image = sharpener.enhance(2.0)
        
        # Extraer texto con Tesseract
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(image, lang='spa', config=custom_config)
        
        print("\n" + "="*70)
        print("🔍 TEXTO RAW EXTRAÍDO POR TESSERACT:")
        print("="*70)
        print(extracted_text)
        print("="*70 + "\n")
        
        # Parsear el texto con nuestro servicio
        from app.services.ocr import parse_ocr_text
        result = parse_ocr_text(extracted_text)
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR EN OCR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generate_document(request: GenerationRequest, db: Session = Depends(get_db)):
    """
    Genera un documento Word usando docxtpl
    
    CAMBIO PRINCIPAL: Ahora usa ServicioDocumentoV2 que implementa docxtpl
    """
    try:
        print("\n" + "="*70)
        print("📝 SOLICITUD DE GENERACIÓN DE DOCUMENTO")
        print("="*70)
        print(f"Plantilla: {request.template_name}")
        print(f"Empresa ID: {request.empresa_id}")
        print(f"Representante ID: {request.representante_id}")
        print(f"Colaborador: {request.colaborador_data.datos_persona.nombre_completo}")
        print("="*70 + "\n")
        
        # Generar documento usando el nuevo servicio
        output_filename = servicio_documento.generar_documento(db, request)
        
        print(f"\n✅ Documento generado exitosamente: {output_filename}\n")
        
        # Retornar archivo para descarga
        return FileResponse(
            output_filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=output_filename
        )
        
    except Exception as e:
        print(f"\n❌ ERROR AL GENERAR DOCUMENTO: {str(e)}\n")
        
        if isinstance(e, HTTPException):
            raise e
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error al generar el documento: {str(e)}"
        )


@router.get("/test")
def test_endpoint():
    """
    Endpoint de prueba para verificar que el servicio está funcionando
    """
    return {
        "status": "ok",
        "message": "Servicio de documentos V2 funcionando correctamente",
        "version": "2.0 - Con docxtpl"
    }
