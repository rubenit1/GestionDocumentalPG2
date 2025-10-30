# app/api/v1/api.py
from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    empresas,
    utils,
    documentos,
    documentos_v2,
    representantes,
    plantillas,
    documentos_onedrive,
    flujo_completo,
    proyectos,
    empresa_proyecto,
    auth,
)

api_router = APIRouter()

# rutas públicas (solo login)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)

# dependencia común: todos los demás requieren estar logueados
require_auth = Depends(auth.get_current_user)

api_router.include_router(
    empresas.router,
    prefix="/empresas",
    tags=["Empresas"],
    dependencies=[require_auth],
)

api_router.include_router(
    representantes.router,
    prefix="/representantes",
    tags=["Representantes Legales"],
    dependencies=[require_auth],
)

api_router.include_router(
    proyectos.router,
    prefix="/proyectos",
    tags=["Proyectos"],
    dependencies=[require_auth],
)

# Documentos V1
api_router.include_router(
    documentos.router,
    prefix="/documentos",
    tags=["Documentos OCR (V1)"],
    dependencies=[require_auth],
)

# Documentos V2
api_router.include_router(
    documentos_v2.router,
    prefix="/documentos-v2",
    tags=["Documentos OCR (V2 - docxtpl)"],
    dependencies=[require_auth],
)

api_router.include_router(
    plantillas.router,
    prefix="/plantillas",
    tags=["Plantillas"],
    dependencies=[require_auth],
)

api_router.include_router(
    utils.router,
    prefix="/utils",
    tags=["Utilidades"],
    dependencies=[require_auth],
)

api_router.include_router(
    flujo_completo.router,
    prefix="/flujo",
    tags=["Flujo Completo"],
    dependencies=[require_auth],
)

api_router.include_router(
    documentos_onedrive.router,
    prefix="/documentos-onedrive",
    tags=["Documentos OneDrive"],
    dependencies=[require_auth],
)

api_router.include_router(
    empresa_proyecto.router,
    prefix="/empresa-proyecto",
    tags=["Empresa-Proyecto"],
    dependencies=[require_auth],
)
