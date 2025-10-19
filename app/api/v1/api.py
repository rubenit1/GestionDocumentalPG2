# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import empresas, utils, documentos, documentos_v2, representantes, plantillas

api_router = APIRouter()
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(representantes.router, prefix="/representantes", tags=["Representantes Legales"])

# Documentos V1 (original) - Mantenemos para compatibilidad
api_router.include_router(documentos.router, prefix="/documentos", tags=["Documentos OCR (V1)"])

# Documentos V2 (con docxtpl) - NUEVO ⭐
api_router.include_router(documentos_v2.router, prefix="/documentos-v2", tags=["Documentos OCR (V2 - docxtpl)"])

api_router.include_router(plantillas.router, prefix="/plantillas", tags=["Plantillas"]) 
api_router.include_router(utils.router, prefix="/utils", tags=["Utilidades"])