# app/core/config.py
"""
Configuración centralizada del sistema
Incluye: Base de datos, Tesseract OCR, Azure AD, OneDrive
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# =============================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "0n4vsb")
DB_HOST = os.getenv("DB_HOST", "RUBENDK")
DB_NAME = os.getenv("DB_NAME", "GestionDocumentalDB")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")


# Azure/OneDrive
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
ONEDRIVE_USER_ID = os.getenv("ONEDRIVE_USER_ID")

SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?driver={DB_DRIVER.replace(' ', '+')}"

# =============================================
# CONFIGURACIÓN DE TESSERACT OCR
# =============================================
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# =============================================
# CONFIGURACIÓN DE AZURE AD Y ONEDRIVE
# =============================================
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
ONEDRIVE_USER_ID = os.getenv("ONEDRIVE_USER_ID")

# Validación de configuración de Azure
if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, ONEDRIVE_USER_ID]):
    print("⚠️ ADVERTENCIA: Variables de Azure/OneDrive no configuradas")
    print("   Los endpoints de OneDrive no funcionarán correctamente")
    print("   Configura .env con las credenciales de Azure AD")

# =============================================
# CONFIGURACIÓN DE AUTENTICACIÓN JWT (FUTURO)
# =============================================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret-key-por-defecto-cambiar-en-produccion")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# =============================================
# RUTAS DE ONEDRIVE (CONFIGURABLES)
# =============================================
ONEDRIVE_PATHS = {
    "contratos": os.getenv("ONEDRIVE_PATH_CONTRATOS", "/Documentos_Legales/Contratos"),
    "minutas": os.getenv("ONEDRIVE_PATH_MINUTAS", "/Documentos_Legales/Minutas"),
    "anexos": os.getenv("ONEDRIVE_PATH_ANEXOS", "/Documentos_Legales/Anexos"),
    "cartas": os.getenv("ONEDRIVE_PATH_CARTAS", "/Documentos_Legales/Cartas"),
    "imagenes": os.getenv("ONEDRIVE_PATH_IMAGENES", "/Documentos_Legales/Imagenes_Originales"),
    "plantillas": os.getenv("ONEDRIVE_PATH_PLANTILLAS", "/Documentos_Legales/Plantillas"),
    "temp": os.getenv("ONEDRIVE_PATH_TEMP", "/Documentos_Legales/Temp")
}

# =============================================
# CONFIGURACIÓN GENERAL
# =============================================
APP_NAME = "Sistema de Gestión Documental"
APP_VERSION = "2.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# =============================================
# FUNCIÓN DE DIAGNÓSTICO
# =============================================
def verificar_configuracion():
    """Verifica que todas las configuraciones necesarias estén presentes"""
    
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN")
    print("="*70)
    
    # Base de datos
    print(f"\n📊 Base de Datos:")
    print(f"  ✓ Host: {DB_HOST}")
    print(f"  ✓ Database: {DB_NAME}")
    print(f"  ✓ User: {DB_USER}")
    
    # Tesseract
    print(f"\n🔍 Tesseract OCR:")
    if os.path.exists(TESSERACT_CMD):
        print(f"  ✓ Path válido: {TESSERACT_CMD}")
    else:
        print(f"  ❌ Path no encontrado: {TESSERACT_CMD}")
    
    # Azure/OneDrive
    print(f"\n☁️ Azure AD / OneDrive:")
    azure_ok = all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, ONEDRIVE_USER_ID])
    if azure_ok:
        print(f"  ✓ Client ID: {AZURE_CLIENT_ID[10:]}...")
        print(f"  ✓ Tenant ID: {AZURE_TENANT_ID[:10]}...")
        print(f"  ✓ OneDrive User: {ONEDRIVE_USER_ID}")
        print(f"  ✓ Secret configurado: Sí")
    else:
        print(f"  ❌ Configuración incompleta")
        print(f"     - Client ID: {'✓' if AZURE_CLIENT_ID else '❌'}")
        print(f"     - Client Secret: {'✓' if AZURE_CLIENT_SECRET else '❌'}")
        print(f"     - Tenant ID: {'✓' if AZURE_TENANT_ID else '❌'}")
        print(f"     - OneDrive User: {'✓' if ONEDRIVE_USER_ID else '❌'}")
    
    print("\n" + "="*70 + "\n")
    
    return azure_ok

# =============================================
# EJECUTAR VERIFICACIÓN AL IMPORTAR (opcional)
# =============================================
if __name__ == "__main__":
    verificar_configuracion()