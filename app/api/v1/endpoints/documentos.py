# --- Imports de FastAPI y dependencias ---
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# --- Imports de librerías ---
import pytesseract
from PIL import Image
import io

# --- Imports de nuestro proyecto ---
from app.db.session import get_db
from app.models.documento import DocumentoProcesado, GenerationRequest
from app.core.config import TESSERACT_CMD
from app.services.documento import ServicioDocumento


router = APIRouter()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
# Creamos una instancia del servicio
servicio_documento = ServicioDocumento()


@router.post("/ocr", response_model=DocumentoProcesado)
async def ocr_extract(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        from app.services.ocr import parse_ocr_text
        extracted_text = pytesseract.image_to_string(image, lang='spa')
        return parse_ocr_text(extracted_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generate_new_document(request: GenerationRequest, db: Session = Depends(get_db)):
    try:
        # --- CORRECCIÓN AQUÍ ---
        # Llamamos al método desde la instancia 'servicio_documento'
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