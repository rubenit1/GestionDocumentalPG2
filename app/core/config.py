# app/core/config.py
# Aquí centralizamos variables de configuración.
import os

# Configuración de Tesseract OCR
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración de Base de Datos
DB_USER = "sa"
DB_PASSWORD = "0n4vsb"
DB_HOST = "RUBENDK"
DB_NAME = "GestionDocumentalDB"
DB_DRIVER = "ODBC Driver 17 for SQL Server"

SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?driver={DB_DRIVER.replace(' ', '+')}"