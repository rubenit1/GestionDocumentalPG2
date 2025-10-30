from email.mime import text
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text 

from app.db.session import get_db
from app.services.auth_service import auth_service

router = APIRouter()

class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str

# Esto le dice a FastAPI/Swagger que el token va en Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ========= LOGIN =========
@router.post("/login")
def login(body: dict, db: Session = Depends(get_db)):
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
        raise HTTPException(
            status_code=400,
            detail="Faltan credenciales"
        )

    data = auth_service.login(db, login_val, password)

    return {
        "ok": True,
        **data  # token + user
    }

# ========= QUIÉN SOY =========
@router.get("/me")
def me(token: str = Depends(oauth2_scheme)):
    """
    Devuelve info del usuario autenticado a partir del JWT.
    Sirve para que el frontend reconstruya sesión.
    """
    user = auth_service.decode_token(token)
    return {
        "ok": True,
        "user": user
    }

# ========= DEPENDENCIAS REUSABLES =========
def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Úsalo en cualquier endpoint que quieras proteger con login.
    Ejemplo:
        dependencies=[Depends(get_current_user)]
    """
    return auth_service.decode_token(token)

def require_roles(roles_permitidos: list[str]):
    """
    Úsalo en endpoints que quieras restringir por rol ("admin", "legal", etc.).
    Ejemplo:
        dependencies=[Depends(require_roles(["admin"]))]
    """
    def checker(user = Depends(get_current_user)):
        if user["rol"] not in roles_permitidos:
            raise HTTPException(
                status_code=403,
                detail="Sin permiso"
            )
        return user
    return checker

# ========= ADMIN: CREAR USUARIO NUEVO =========
@router.post(
    "/crear-usuario",
    dependencies=[Depends(require_roles(["admin"]))],
)
def crear_usuario(body: dict, db: Session = Depends(get_db)):
    """
    Body esperado:
    {
        "username": "nuevoUser",
        "email": "nuevo@empresa.com",
        "password": "ClaveTemporalInicial!",
        "rol": "legal"   # o "admin", etc.
    }
    """
    username = body.get("username")
    email = body.get("email")
    password_plano = body.get("password")
    rol = body.get("rol")

    if not username or not email or not password_plano or not rol:
        raise HTTPException(
            status_code=400,
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

# ========= ADMIN: RESET PASSWORD =========
@router.post(
    "/reset-password",
    dependencies=[Depends(require_roles(["admin"]))],
)
def reset_password(body: dict, db: Session = Depends(get_db)):
    """
    Body esperado:
    {
        "user_id": 1,
        "new_password": "MiClaveFinalSegura2025!"
    }
    """
    user_id = body.get("user_id")
    nueva = body.get("new_password")

    if not user_id or not nueva:
        raise HTTPException(
            status_code=400,
            detail="Faltan campos"
        )

    actualizado = auth_service.reset_password(db, user_id, nueva)

    return {
        "ok": True,
        "user": actualizado
    }

@router.get("/usuarios", dependencies=[Depends(require_roles(["admin"]))], tags=["Auth"])
def listar_usuarios_activos(db: Session = Depends(get_db)):
    """
    Lista solo usuarios activos usando el SP unificado.
    """
    try:
        rows = db.execute(
            text("EXEC dbo.sp_Usuarios_CRUD @accion = :accion"),
            {"accion": "LIST"}
        ).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {str(e)}")

    return {"ok": True, "items": [dict(r) for r in rows]}


@router.get("/usuarios/todos", dependencies=[Depends(require_roles(["admin"]))], tags=["Auth"])
def listar_usuarios_todos(db: Session = Depends(get_db)):
    """
    Lista todos los usuarios (activos e inactivos).
    """
    try:
        rows = db.execute(
            text("EXEC dbo.sp_Usuarios_CRUD @accion = :accion"),
            {"accion": "LIST_ALL"}
        ).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios (todos): {str(e)}")

    return {"ok": True, "items": [dict(r) for r in rows]}


@router.delete("/usuarios/{user_id}", dependencies=[Depends(require_roles(["admin"]))], tags=["Auth"])
def desactivar_usuario(user_id: int, db: Session = Depends(get_db)):
    """
    Borrado lógico (is_active = 0) usando el SP unificado.
    """
    try:
        row = db.execute(
            text("""
                EXEC dbo.sp_Usuarios_CRUD
                    @accion = :accion,
                    @id = :id
            """),
            {"accion": "DISABLE", "id": user_id}
        ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desactivar usuario: {str(e)}")

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"ok": True, "user": dict(row)}

@router.post("/usuarios/reset-password", dependencies=[Depends(require_roles(["admin"]))], tags=["Auth"])
def resetear_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Cambia la contraseña de un usuario existente.
    - Requiere rol admin.
    - Encripta con bcrypt antes de guardar.
    - Usa el SP unificado sp_Usuarios_CRUD (@accion='UPDATE_PASSWORD').
    """
    try:
        nuevo_hash = bcrypt.hash(request.new_password)

        row = db.execute(
            text("""
                EXEC dbo.sp_Usuarios_CRUD
                    @accion = :accion,
                    @id = :id,
                    @password_hash = :ph
            """),
            {"accion": "UPDATE_PASSWORD", "id": request.user_id, "ph": nuevo_hash}
        ).mappings().first()

        db.commit()

        if not row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"ok": True, "user": dict(row)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar la contraseña: {str(e)}")