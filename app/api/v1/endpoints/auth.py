from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List # Para la respuesta de lista

from app.db.session import get_db
# Importar el servicio refactorizado
from app.services.auth_service import auth_service
# Importar los nuevos modelos Pydantic
from app.models.usuario import (
    UserCreateRequest,
    UserUpdateRequest,
    PasswordResetRequest,
    UserPublic,
    TokenData,
    LoginResponse
)

router = APIRouter()

# Esto le dice a FastAPI/Swagger que el token va en Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ========= LOGIN =========
@router.post("/login", response_model=LoginResponse)
def login(body: dict = Body(...), db: Session = Depends(get_db)):
    """
    Body esperado:
    {
        "login": "admin@empresa.com" o "admin",
        "password": "Temporal123!"
    }
    """
    login_val = body.get("login")
    password = body.get("password")

    if not login_val or not password:
        raise HTTPException(status_code=400, detail="Faltan credenciales")

    token, user_public = auth_service.login(db, login_val, password)

    return LoginResponse(ok=True, token=token, user=user_public)

# ========= DEPENDENCIAS REUSABLES =========
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Úsalo en cualquier endpoint que quieras proteger con login."""
    return auth_service.decode_token(token)

def require_roles(roles_permitidos: list[str]):
    """Restringe endpoints por rol ("admin", "legal", etc.)."""
    def checker(user: TokenData = Depends(get_current_user)):
        if user.rol not in roles_permitidos:
            raise HTTPException(status_code=403, detail="Sin permiso")
        return user
    return checker

# ========= QUIÉN SOY (Protegido) =========
@router.get("/me")
def me(current_user: TokenData = Depends(get_current_user)): # <--- CORREGIDO
    """
    Devuelve info del usuario autenticado a partir del JWT.
    (La dependencia get_current_user ya hace la validación)
    """
    return {"ok": True, "user": current_user}


# ========= ADMIN: CREAR USUARIO NUEVO =========
@router.post(
    "/crear-usuario",
    response_model=UserPublic,
    dependencies=[Depends(require_roles(["admin"]))],
)
def crear_usuario(user_data: UserCreateRequest, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario.
    El body debe coincidir con el modelo UserCreateRequest.
    """
    # La lógica de hashear y llamar al SP está en el servicio
    nuevo_usuario = auth_service.crear_usuario(db, user_data)
    
    # El servicio ya devuelve el modelo público traducido
    return nuevo_usuario

# ========= ADMIN: LISTAR USUARIOS ACTIVOS =========
@router.get(
    "/usuarios",
    response_model=List[UserPublic],
    dependencies=[Depends(require_roles(["admin"]))],
)
def listar_usuarios_activos(db: Session = Depends(get_db)):
    """Lista solo usuarios activos."""
    usuarios = auth_service.listar_usuarios(db, todos=False)
    return usuarios

# ========= ADMIN: LISTAR TODOS LOS USUARIOS =========
@router.get(
    "/usuarios/todos",
    response_model=List[UserPublic],
    dependencies=[Depends(require_roles(["admin"]))],
)
def listar_usuarios_todos(db: Session = Depends(get_db)):
    """Lista todos los usuarios (activos e inactivos)."""
    usuarios = auth_service.listar_usuarios(db, todos=True)
    return usuarios

# ========= ADMIN: EDITAR USUARIO =========
@router.put(
    "/usuarios/{user_id}",
    response_model=UserPublic,
    dependencies=[Depends(require_roles(["admin"]))],
)
def editar_usuario(user_id: int, user_data: UserUpdateRequest, db: Session = Depends(get_db)):
    """Actualiza los datos de un usuario (username, email, nombre, rol)."""
    usuario_actualizado = auth_service.editar_usuario(db, user_id, user_data)
    return usuario_actualizado

# ========= ADMIN: DESACTIVAR USUARIO =========
@router.delete(
    "/usuarios/{user_id}",
    response_model=UserPublic,
    dependencies=[Depends(require_roles(["admin"]))],
)
def desactivar_usuario(user_id: int, db: Session = Depends(get_db)):
    """Borrado lógico (is_active = 0) de un usuario."""
    usuario_desactivado = auth_service.desactivar_usuario(db, user_id)
    return usuario_desactivado

# ========= ADMIN: RESET PASSWORD =========
@router.post(
    "/usuarios/reset-password",
    response_model=UserPublic,
    dependencies=[Depends(require_roles(["admin"]))],
)
def resetear_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Cambia la contraseña de un usuario existente."""
    usuario_actualizado = auth_service.reset_password(db, request)
    return usuario_actualizado

