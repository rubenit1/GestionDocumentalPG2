# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import empresas, utils, documentos, representantes, plantillas # <-- Añadir plantillas

api_router = APIRouter()
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(representantes.router, prefix="/representantes", tags=["Representantes Legales"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["Documentos y OCR"])
api_router.include_router(plantillas.router, prefix="/plantillas", tags=["Plantillas"]) 
api_router.include_router(utils.router, prefix="/utils", tags=["Utilidades"])