from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service

router = APIRouter()

# Swagger/fastapi docs saben que el token viene como Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# === LOGIN ===
@router.post("/login")
def login(body: dict, db: Session = Depends(get_db)):
    """
    body esperado:
    {
        "login": "usuario_o_email",
        "password": "Clave"
    }
    """
    login_val = body.get("login")
    password = body.get("password")

    if not login_val or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faltan credenciales"
        )

    data = auth_service.login(db, login_val, password)

    return {
        "ok": True,
        **data  # incluye token + user
    }

# === QUIEN SOY ===
@router.get("/me")
def me(token: str = Depends(oauth2_scheme)):
    user = auth_service.decode_token(token)
    return {
        "ok": True,
        "user": user
    }

# === DEPENDENCIAS PARA PROTEGER RUTAS ===
def get_current_user(token: str = Depends(oauth2_scheme)):
    return auth_service.decode_token(token)

def require_roles(roles_permitidos: list[str]):
    def checker(user = Depends(get_current_user)):
        if user["rol"] not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permiso"
            )
        return user
    return checker

# === ADMIN: CREAR USUARIO ===
@router.post(
    "/crear-usuario",
    dependencies=[Depends(require_roles(["admin"]))],
)
def crear_usuario(body: dict, db: Session = Depends(get_db)):
    """
    {
        "username": "nuevoUser",
        "email": "nuevo@empresa.com",
        "password": "ClaveTemporal123!",
        "rol": "legal"
    }
    """
    username = body.get("username")
    email = body.get("email")
    password_plano = body.get("password")
    rol = body.get("rol")

    if not username or not email or not password_plano or not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faltan campos obligatorios"
        )

    nuevo = auth_service.crear_usuario(
        db,
        username=username,
        email=email,
        password_plano=password_plano,
        rol=rol
    )

    return {
        "ok": True,
        "user": nuevo
    }

# === ADMIN: RESET PASSWORD ===
@router.post(
    "/reset-password",
    dependencies=[Depends(require_roles(["admin"]))],
)
def reset_password(body: dict, db: Session = Depends(get_db)):
    """
    {
        "user_id": 1,
        "new_password": "MiClaveFinalSegura2025!"
    }
    """
    user_id = body.get("user_id")
    nueva = body.get("new_password")

    if not user_id or not nueva:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faltan campos"
        )

    actualizado = auth_service.reset_password(db, user_id, nueva)

    return {
        "ok": True,
        "user": actualizado
    }
