# main.py
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import datetime
import shutil 
import pytesseract
from PIL import Image
import io
import re
import num2words
import docx

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Importación de CORS movida al inicio
from fastapi.middleware.cors import CORSMiddleware

# --- Importaciones para SQL Server (SQLAlchemy) ---
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# --- Importaciones para MongoDB (PyMongo) ---
import pymongo
from pymongo.errors import ConnectionFailure

# --- CONFIGURACIÓN DE CONEXIONES ---
SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://sa:0n4vsb@RUBENDK/GestionDocumentalDB?driver=ODBC+Driver+17+for+SQL+Server"
MONGO_URI = "mongodb://gestor_app:Avianca2014$$@localhost:27017/?authSource=GestionDocumentalDB"

# --- CÓDIGO PARA SQL SERVER ---
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    class Empresa(Base):
        __tablename__ = "empresa"
        id = Column(Integer, primary_key=True, index=True)
        razon_social = Column(String(255), unique=True, index=True)

    class Persona(Base):
        __tablename__ = "persona"
        id = Column(Integer, primary_key=True, index=True)
        cui = Column(String(15), unique=True, index=True)
        nombre_completo = Column(String(255))
        fecha_nacimiento = Column(Date)
        direccion = Column(String(500))

    Base.metadata.create_all(bind=engine) 

    def get_db_sql():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
except Exception as e:
    print(f"❌ ERROR AL CONFIGURAR SQL SERVER: {e}")
    exit()

# --- CÓDIGO PARA MONGODB ---
try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    mongo_client.admin.command('ping')
    print("✅ Conexión a MongoDB exitosa.")
    db_mongo = mongo_client["GestionDocumentalDB"]
except ConnectionFailure as e:
    print(f"❌ Error de conexión a MongoDB: {e}")
    mongo_client = None
    db_mongo = None

# --- MODELOS DE DATOS DE LA API (Pydantic) ---
class PersonaData(BaseModel):
    cui: str
    nombre_completo: str
    fecha_nacimiento: str
    direccion: str

class ContratoData(BaseModel):
    tipo_contrato: str
    fecha_inicio: str
    fecha_fin: str
    monto: float
    descripcion_adicional: Optional[str] = None

class DocumentoProcesado(BaseModel):
    empresa_contratante: str
    datos_persona: PersonaData
    datos_contrato: ContratoData

# --- APLICACIÓN FastAPI ---
app = FastAPI(title="API de Gestión Documental", version="1.0.0")

# ================== CONFIGURACIÓN DE CORS (POSICIÓN CORRECTA) ==================
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ==============================================================================


# --- ENDPOINTS DE LA API ---

@app.post("/api/v1/contracts/process")
def procesar_documento(documento: DocumentoProcesado, db_sql: Session = Depends(get_db_sql)):
    # ... (la lógica de este endpoint no cambia)
    empresa = db_sql.query(Empresa).filter(Empresa.razon_social == documento.empresa_contratante).first()
    if not empresa:
        empresa = Empresa(razon_social=documento.empresa_contratante)
        db_sql.add(empresa)
        db_sql.commit()
        db_sql.refresh(empresa)
    
    persona = db_sql.query(Persona).filter(Persona.cui == documento.datos_persona.cui).first()
    if not persona:
        fecha_nac_obj = datetime.datetime.strptime(documento.datos_persona.fecha_nacimiento, "%d/%m/%Y").date()
        persona = Persona(
            cui=documento.datos_persona.cui,
            nombre_completo=documento.datos_persona.nombre_completo,
            fecha_nacimiento=fecha_nac_obj,
            direccion=documento.datos_persona.direccion
        )
        db_sql.add(persona)
        db_sql.commit()
        db_sql.refresh(persona)

    if not db_mongo:
        raise HTTPException(status_code=500, detail="No se pudo conectar a MongoDB.")

    contratos_collection = db_mongo["contratos"]
    
    contrato_documento = {
        "empresa_id_sql": empresa.id,
        "persona_id_sql": persona.id,
        "tipo_contrato": documento.datos_contrato.tipo_contrato,
        "fecha_inicio": datetime.datetime.strptime(documento.datos_contrato.fecha_inicio, "%d/%m/%Y"),
        "fecha_fin": datetime.datetime.strptime(documento.datos_contrato.fecha_fin, "%d/%m/%Y"),
        "monto": documento.datos_contrato.monto,
        "descripcion_adicional": documento.datos_contrato.descripcion_adicional,
        "fecha_creacion_registro": datetime.datetime.now()
    }
    
    result = contratos_collection.insert_one(contrato_documento)
    
    return {
        "status": "éxito",
        "message": "Datos guardados en SQL y registro de contrato creado en MongoDB.",
        "id_contrato_mongo": str(result.inserted_id)
    }

# ================== FUNCIÓN AUXILIAR PARA PARSEAR ==================
# main.py

# ... (importaciones y demás código)

# main.py

# ... (tus otras importaciones)
import re
from num2words import num2words

# ... (el resto de tu código)

# ================== REEMPLAZA ESTA FUNCIÓN COMPLETA ==================
def parse_ocr_text(text):
    """
    Usa expresiones regulares para extraer datos, formatea los datos
    según los requisitos finales y maneja el contrato indefinido.
    """
    data = {}
    
    # Patrones de búsqueda
    patterns = [
        ('empresa_contratante', r"EMPRESA\s+([^\n]+)"),
        ('nombre_completo', r"COLABORADOR\s+([^\n]+)"),
        ('cui', r"DPI\s*/PASAPORTE\s+(\d+)"),
        ('direccion', r"DIRECCIÓN\s+([^\n]+)"),
        ('fecha_inicio', r"FECHA DE INICIO\s+([^\n]+)"),
        ('fecha_fin', r"FECHA DE FINALIZACIÓN\s+([^\n]+)"),
        ('monto', r"HONORARIOS POR PAGAR\s+([\d,]+\.\d{2})"),
        ('posicion', r"POSICIÓN\s+([^\n]+)"),
    ]

    for key, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key == 'monto':
                value = value.replace(',', '')
            data[key] = value

    # --- LÓGICA DE PROCESAMIENTO AJUSTADA ---

    # 1. Procesar el Monto
    monto_numero = 0.0
    monto_en_letras = "CERO QUETZALES EXACTOS"
    monto_formateado = "Q.0.00" # <-- VALOR POR DEFECTO AJUSTADO
    
    if data.get("monto"):
        try:
            monto_numero = float(data["monto"])
            # Formatear como moneda con el punto después de la Q
            monto_formateado = f"Q.{monto_numero:,.2f}" # <-- CAMBIO DE FORMATO
            # Convertir a letras
            parte_entera = int(monto_numero)
            monto_en_letras = num2words(parte_entera, lang='es').upper() + " QUETZALES EXACTOS"
        except (ValueError, TypeError):
            pass

    # 2. Procesar Fecha de Finalización
    fecha_fin_texto = data.get("fecha_fin") # Obtenemos el valor, puede ser None
    
    # Si la fecha no se encontró (es None) o si contiene "indefinido"
    if not fecha_fin_texto or "indefinido" in fecha_fin_texto.lower():
        fecha_fin_texto = "Contrato Indefinido"

    # --- Construcción del JSON Final ---
    structured_data = {
        "empresa_contratante": data.get("empresa_contratante", ""),
        "datos_persona": {
            "cui": data.get("cui", ""),
            "nombre_completo": data.get("nombre_completo", ""),
            "direccion": data.get("direccion", ""),
        },
        "datos_contrato": {
            "tipo_contrato": data.get("posicion", "Servicios Profesionales"),
            "fecha_inicio": data.get("fecha_inicio", ""),
            "fecha_fin": fecha_fin_texto,
            "monto": monto_formateado,
            "monto_en_letras": monto_en_letras,
            "descripcion_adicional": f"Posición: {data.get('posicion', 'N/A')}"
        }
    }
    
    return structured_data
# ========================================================================

# ... (importaciones y demás código)

# main.py

# ... (tus otras importaciones)
import re
from num2words import num2words

# ... (el resto de tu código)

# ================== REEMPLAZA ESTA FUNCIÓN COMPLETA ==================
# ================== REEMPLAZA ESTA FUNCIÓN COMPLETA ==================
def parse_ocr_text(text):
    """
    Versión final del parser, con expresiones regulares más tolerantes
    para manejar errores comunes del OCR.
    """
    data = {}
    
    # Patrones de búsqueda más flexibles
    patterns = [
        ('empresa_contratante', r"EMPRESA\s+([^\n]+)"),
        ('nombre_completo', r"COLABORADOR\s+([^\n]+)"),
        # Tolera "DPI /PASAPORTE" o "DPI JPASAPORTE"
        ('cui', r"DPI\s*[/J]?\s*PASAPORTE\s+(\d+)"),
        ('direccion', r"DIRECCIÓN\s+([^\n]+)"),
        ('fecha_inicio', r"FECHA DE INICIO\s+([^\n]+)"),
        ('fecha_fin', r"FECHA DE FINALIZACIÓN\s+([^\n]+)"),
        # Tolera "PAGAR" o "PACAR"
        ('monto', r"HONORARIOS POR PA[GC]AR\s+([\d,]+\.\d{2})"),
        ('posicion', r"POSICIÓN\s+([^\n]+)"),
    ]

    for key, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key == 'monto':
                value = value.replace(',', '')
            data[key] = value

    # --- Lógica de Procesamiento ---
    monto_numero = 0.0
    monto_en_letras = "CERO QUETZALES EXACTOS"
    monto_formateado = "Q.0.00"
    
    if data.get("monto"):
        try:
            monto_numero = float(data["monto"])
            monto_formateado = f"Q.{monto_numero:,.2f}"
            parte_entera = int(monto_numero)
            monto_en_letras = num2words(parte_entera, lang='es').upper() + " QUETZALES EXACTOS"
        except (ValueError, TypeError):
            pass

    fecha_fin_texto = data.get("fecha_fin")
    if not fecha_fin_texto or "indefinido" in fecha_fin_texto.lower():
        fecha_fin_texto = "Contrato Indefinido"

    # --- Construcción del JSON Final ---
    structured_data = {
        "empresa_contratante": data.get("empresa_contratante", ""),
        "datos_persona": {
            "cui": data.get("cui", ""),
            "nombre_completo": data.get("nombre_completo", ""),
            "direccion": data.get("direccion", ""),
        },
        "datos_contrato": {
            "tipo_contrato": data.get("posicion", "Servicios Profesionales"),
            "fecha_inicio": data.get("fecha_inicio", ""),
            "fecha_fin": fecha_fin_texto,
            "monto": monto_formateado,
            "monto_en_letras": monto_en_letras,
            "descripcion_adicional": f"Posición: {data.get('posicion', 'N/A')}"
        }
    }
    
    return structured_data
# ========================================================================
# ================== ENDPOINT DE OCR FINAL ==================
@app.post("/api/v1/ocr/extract-data")
async def extract_data_from_image(file: UploadFile = File(...)):
    """
    Recibe una imagen, la procesa con Tesseract OCR,
    parsea el texto y devuelve un JSON estructurado.
    """
    print(f"📄 Imagen '{file.filename}' recibida para procesamiento OCR real.")
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        extracted_text = pytesseract.image_to_string(image, lang='spa')
        
        print("--- Texto Extraído por Tesseract ---")
        print(extracted_text)
        print("------------------------------------")

        # ¡Ahora usamos nuestra nueva función para parsear el texto!
        response_data = parse_ocr_text(extracted_text)
        
        print("--- JSON Estructurado ---")
        print(response_data)
        print("-------------------------")

        return response_data

    except Exception as e:
        print(f"❌ Error durante el procesamiento OCR: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen con OCR: {e}")