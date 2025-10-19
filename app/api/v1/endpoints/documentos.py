# app/api/v1/endpoints/documentos.py
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import pytesseract
from PIL import Image, ImageEnhance  # ← Importación correcta aquí
import io

from app.db.session import get_db
from app.models.documento import DocumentoProcesado, GenerationRequest
from app.core.config import TESSERACT_CMD
from app.services.documento import ServicioDocumento

router = APIRouter()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
servicio_documento = ServicioDocumento()


@router.post("/ocr", response_model=DocumentoProcesado)
async def ocr_extract(file: UploadFile = File(...)):
    """
    Endpoint de OCR con preprocesamiento de imagen.
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
        # PSM 6 = Asume un bloque uniforme de texto (ideal para tablas)
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
def generate_new_document(request: GenerationRequest, db: Session = Depends(get_db)):
    try:
        output_filename = servicio_documento.generar_documento(db, request)
        
        return FileResponse(
            output_filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=output_filename
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error al generar el documento: {str(e)}")