from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.hash import bcrypt
from jose import jwt, JWTError

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
)

class AuthService:
    def _actualizar_hash_en_bd(self, db: Session, user_id: int, new_hash: str):
        db.execute(
            text("""
                UPDATE dbo.usuarios
                SET password_hash = :new_hash
                WHERE id = :user_id
            """),
            {
                "new_hash": new_hash,
                "user_id": user_id
            }
        )
        db.commit()

    def login(self, db: Session, login: str, password: str):
        # 1. Validar que tenemos config JWT cargada
        if not JWT_SECRET or JWT_SECRET == "change_me":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_SECRET no está configurado en el entorno"
            )

        # 2. Intentar leer el usuario desde BD
        try:
            result = db.execute(
                text("EXEC dbo.sp_Auth_Login @login=:login"),
                {"login": login}
            ).mappings().first()
        except Exception as e:
            # falla al ejecutar el SP o al conectar a la BD
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al consultar BD/sp_Auth_Login: {str(e)}"
            )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )

        # Ahora asegurarnos que las columnas que esperamos realmente llegaron
        campos_esperados = ["id", "username", "email", "password_hash", "rol", "is_active"]
        for campo in campos_esperados:
            if campo not in result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"El SP no devolvió la columna '{campo}'"
                )

        if not result["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )

        user_id = result["id"]
        stored_value = result["password_hash"]

        # 3. Lógica de verificación / migración
        password_ok = False
        is_bcrypt = False

        try:
            if stored_value and str(stored_value).startswith(("$2a$", "$2b$", "$2y$")):
                is_bcrypt = True
                if bcrypt.verify(password, stored_value):
                    password_ok = True
        except Exception as e:
            # bcrypt lanzó error raro
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verificando bcrypt: {str(e)}"
            )

        # fallback: texto plano temporal
        if not password_ok and not is_bcrypt:
            if password == stored_value:
                password_ok = True
                try:
                    nuevo_hash = bcrypt.hash(password)
                    self._actualizar_hash_en_bd(db, user_id, nuevo_hash)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"No se pudo migrar password a bcrypt: {str(e)}"
                    )

        if not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        # 4. Construir token JWT
        try:
            expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
            payload = {
                "sub": str(result["id"]),
                "username": result["username"],
                "rol": result["rol"],
                "exp": expire,
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generando JWT: {str(e)}"
            )

        # 5. Responder
        return {
            "token": token,
            "user": {
                "id": result["id"],
                "username": result["username"],
                "email": result["email"],
                "nombre_completo": result.get("nombre_completo"),
                "rol": result["rol"],
            }
        }

    def decode_token(self, token: str):
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "id": int(data["sub"]),
                "username": data["username"],
                "rol": data["rol"],
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )

    def crear_usuario(self, db: Session, username: str, email: str, password_plano: str, rol: str):
        from passlib.hash import bcrypt
        existente = db.execute(
            text("""
                SELECT TOP 1 id FROM dbo.usuarios
                WHERE username = :u OR email = :e
            """),
            {"u": username, "e": email}
        ).first()

        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario o correo ya existe"
            )

        hashed = bcrypt.hash(password_plano)

        result = db.execute(
            text("""
                INSERT INTO dbo.usuarios (username, email, password_hash, rol, is_active)
                OUTPUT INSERTED.id, INSERTED.username, INSERTED.email, INSERTED.rol, INSERTED.is_active
                VALUES (:u, :e, :p, :r, 1)
            """),
            {
                "u": username,
                "e": email,
                "p": hashed,
                "r": rol
            }
        ).mappings().first()

        db.commit()

        return {
            "id": result["id"],
            "username": result["username"],
            "email": result["email"],
            "rol": result["rol"],
            "is_active": result["is_active"],
        }

    def reset_password(self, db: Session, user_id: int, nueva_clave: str):
        from passlib.hash import bcrypt
        hashed = bcrypt.hash(nueva_clave)

        result = db.execute(
            text("""
                UPDATE dbo.usuarios
                SET password_hash = :p
                OUTPUT INSERTED.id, INSERTED.username, INSERTED.email, INSERTED.rol, INSERTED.is_active
                WHERE id = :id
            """),
            {"p": hashed, "id": user_id}
        ).mappings().first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        db.commit()

        return {
            "id": result["id"],
            "username": result["username"],
            "email": result["email"],
            "rol": result["rol"],
            "is_active": result["is_active"],
        }

auth_service = AuthService()
# =============================================