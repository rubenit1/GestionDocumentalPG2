# app/api/v1/endpoints/documentos_v2.py
"""
Endpoint actualizado usando docxtpl para generación de documentos
VERSIÓN MEJORADA - Con mejor preprocesamiento OCR
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io

from app.db.session import get_db
from app.models.documento import DocumentoProcesado, GenerationRequest
from app.core.config import TESSERACT_CMD
from app.services.documento_v2 import ServicioDocumentoV2

router = APIRouter()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
servicio_documento = ServicioDocumentoV2()


@router.post("/ocr", response_model=DocumentoProcesado)
async def ocr_extract(file: UploadFile = File(...)):
    """
    Endpoint de OCR con preprocesamiento MEJORADO de imagen.
    Optimizado para detectar números en tablas (como edad).
    
    MEJORAS:
    - Contraste más agresivo (2.5x)
    - Brillo ajustado (+20%)
    - Nitidez aumentada (3.0x)
    - Filtro SHARPEN adicional
    """
    print(f"📄 Procesando imagen: {file.filename}")
    
    try:
        # Leer la imagen
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # ===== PREPROCESAMIENTO MEJORADO =====
        
        # 1. Convertir a escala de grises
        image = image.convert('L')
        
        # 2. Aumentar contraste (MÁS AGRESIVO)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)  # ⬆ Aumentado de 2.0 a 2.5
        
        # 3. Ajustar brillo ligeramente
        brightness = ImageEnhance.Brightness(image)
        image = brightness.enhance(1.2)  # ➕ NUEVO
        
        # 4. Aumentar nitidez (MÁS AGRESIVO)
        sharpener = ImageEnhance.Sharpness(image)
        image = sharpener.enhance(3.0)  # ⬆ Aumentado de 2.0 a 3.0
        
        # 5. Aplicar filtro de nitidez adicional
        image = image.filter(ImageFilter.SHARPEN)  # ➕ NUEVO
        
        # ===== EXTRACCIÓN DE TEXTO =====
        
        # INTENTAR MÚLTIPLES CONFIGURACIONES DE TESSERACT
        
        # Primer intento: PSM 6 (bloque uniforme de texto)
        custom_config_1 = r'--oem 3 --psm 6'
        extracted_text_1 = pytesseract.image_to_string(image, lang='spa', config=custom_config_1)
        
        # Segundo intento: PSM 4 (columna única de texto - mejor para tablas)
        custom_config_2 = r'--oem 3 --psm 4'
        extracted_text_2 = pytesseract.image_to_string(image, lang='spa', config=custom_config_2)
        
        # Tercer intento: PSM 11 (encontrar texto disperso - mejor para celdas)
        custom_config_3 = r'--oem 3 --psm 11'
        extracted_text_3 = pytesseract.image_to_string(image, lang='spa', config=custom_config_3)
        
        # Combinar resultados (el más largo suele ser el más completo)
        textos = [extracted_text_1, extracted_text_2, extracted_text_3]
        extracted_text = max(textos, key=len)
        
        print("\n" + "="*70)
        print("🔍 TEXTO RAW EXTRAÍDO POR TESSERACT:")
        print("="*70)
        print(f"[PSM 6 - {len(extracted_text_1)} chars]")
        print(f"[PSM 4 - {len(extracted_text_2)} chars]")
        print(f"[PSM 11 - {len(extracted_text_3)} chars]")
        print(f"\n📌 Usando el más completo:")
        print(extracted_text)
        print("="*70 + "\n")
        
        # Parsear el texto con nuestro servicio MEJORADO
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
        "version": "2.1 - Con docxtpl + OCR mejorado"
    }