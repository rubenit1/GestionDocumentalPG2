# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import empresas, utils, documentos, documentos_v2, representantes, plantillas, documentos_onedrive, flujo_completo,proyectos

api_router = APIRouter()
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(representantes.router, prefix="/representantes", tags=["Representantes Legales"])

api_router.include_router(proyectos.router, prefix="/proyectos", tags=["Proyectos"])

# Documentos V1 (original) - Mantenemos para compatibilidad
api_router.include_router(documentos.router, prefix="/documentos", tags=["Documentos OCR (V1)"])

# Documentos V2 (con docxtpl) -
api_router.include_router(documentos_v2.router, prefix="/documentos-v2", tags=["Documentos OCR (V2 - docxtpl)"])

api_router.include_router(plantillas.router, prefix="/plantillas", tags=["Plantillas"]) 
api_router.include_router(utils.router, prefix="/utils", tags=["Utilidades"])

api_router.include_router(
    flujo_completo.router,
    prefix="/flujo",
    tags=["Flujo Completo"]
)

api_router.include_router(
    documentos_onedrive.router, 
    prefix="/documentos-onedrive", 
    tags=["Documentos OneDrive"]
)

