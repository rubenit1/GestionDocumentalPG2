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
    return repo.get_all(db)

@router.post("/upload")
async def upload_plantilla(
    file: UploadFile = File(...),
    nombre: str = Form(...),
    descripcion: str = Form(...),
    categoria: str = Form(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .docx")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"plantilla_{timestamp}.docx"
    file_path = os.path.join("templates", nombre_archivo)
    os.makedirs("templates", exist_ok=True)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Lógica para extraer placeholders...
    doc = docx.Document(file_path)
    placeholders = set()
    # ... (código para extraer placeholders de párrafos y tablas) ...
    campos_json = json.dumps(list(placeholders))
    
    repo.create(db, nombre, descripcion, nombre_archivo, categoria, campos_json)
    
    return {"message": "Plantilla subida exitosamente", "nombre_archivo": nombre_archivo}