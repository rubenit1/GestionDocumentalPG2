# app/api/v1/endpoints/plantillas.py
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import datetime
import json
import re
import docx

from app.db.session import get_db
from app.repository.plantilla import PlantillaRepository
from app.models.plantilla import PlantillaSchema

router = APIRouter()
repo = PlantillaRepository()

@router.get("/", response_model=List[PlantillaSchema])
def get_all_plantillas(db: Session = Depends(get_db)):
    """
    Obtiene todas las plantillas activas. (Lectura, no necesita commit).
    """
    return repo.get_all(db)

@router.post("/upload")
async def upload_plantilla(
    file: UploadFile = File(...),
    nombre: str = Form(...),
    descripcion: str = Form(...),
    categoria: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Sube un archivo .docx, extrae sus placeholders y lo registra en la BD.
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .docx")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"plantilla_{timestamp}.docx"
    file_path = os.path.join("templates", nombre_archivo)
    os.makedirs("templates", exist_ok=True)

    contents = await file.read()
    
    try:
        # 1. Escribir el archivo en el disco
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 2. Lógica para extraer placeholders...
        doc = docx.Document(file_path)
        placeholders = set()
        # ... (código para extraer placeholders de párrafos y tablas) ...
        # (Asegúrate de que esta lógica esté implementada)
        campos_json = json.dumps(list(placeholders))
        
        # 3. Guardar el registro en la base de datos
        repo.create(db, nombre, descripcion, nombre_archivo, categoria, campos_json)
        
        # 4. CONFIRMAR LA TRANSACCIÓN
        db.commit()
        
        return {"message": "Plantilla subida exitosamente", "nombre_archivo": nombre_archivo}

    except Exception as e:
        # 5. DESHACER LA TRANSACCIÓN DE BD
        db.rollback()
        
        # 6. Limpiar el archivo guardado si la BD falló
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Limpieza: Se eliminó el archivo {file_path} por error en BD.")
            except OSError as ex:
                print(f"Error al limpiar archivo {file_path}: {ex}")
                
        raise HTTPException(status_code=500, detail=f"Error al subir plantilla: {str(e)}")