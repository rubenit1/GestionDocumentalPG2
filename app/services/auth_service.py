from datetime import datetime, timedelta
from fastapi import HTTPException
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
        """
        Actualiza el hash de contraseña de un usuario en la base de datos.
        """
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
        """
        Autentica al usuario y devuelve un token JWT junto con sus datos básicos.

        Flujo:
        - Obtiene el usuario mediante el SP dbo.sp_Auth_Login (por username o email).
        - Verifica la contraseña con bcrypt.verify().
        - Genera y devuelve el JWT con la información básica del usuario.
        """

        # 1. Validar configuración del JWT
        if not JWT_SECRET or JWT_SECRET == "change_me":
            raise HTTPException(
                status_code=500,
                detail="JWT_SECRET no está configurado en el entorno"
            )

        # 2. Consultar el usuario en la BD
        try:
            result = db.execute(
                text("EXEC dbo.sp_Auth_Login @login=:login"),
                {"login": login}
            ).mappings().first()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al consultar BD/sp_Auth_Login: {str(e)}"
            )

        if not result:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        # 3. Validar columnas esperadas
        campos_esperados = ["id", "username", "email", "password_hash", "rol", "is_active"]
        for campo in campos_esperados:
            if campo not in result:
                raise HTTPException(
                    status_code=500,
                    detail=f"El SP no devolvió la columna '{campo}'"
                )

        if not result["is_active"]:
            raise HTTPException(
                status_code=403,
                detail="Usuario inactivo"
            )

        user_id = result["id"]
        stored_value = result["password_hash"] or ""

        # 4. Verificar bcrypt
        try:
            if not bcrypt.verify(password, stored_value):
                raise HTTPException(
                    status_code=401,
                    detail="Credenciales inválidas"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error verificando bcrypt: {str(e)}"
            )

        # 5. Generar token JWT
        try:
            expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
            payload = {
                "sub": str(user_id),
                "username": result["username"],
                "rol": result["rol"],
                "exp": expire,
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generando JWT: {str(e)}"
            )

        # 6. Respuesta final
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
        """
        Valida el JWT que manda el cliente y regresa la identidad.
        """
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "id": int(data["sub"]),
                "username": data["username"],
                "rol": data["rol"],
            }
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Token inválido o expirado"
            )

    def crear_usuario(self, db: Session, username: str, email: str, password_plano: str, rol: str):
        """
        Crea un usuario nuevo con contraseña en bcrypt.
        Solo debería usarse desde un endpoint protegido por rol "admin".
        """
        existente = db.execute(
            text("""
                SELECT TOP 1 id FROM dbo.usuarios
                WHERE username = :u OR email = :e
            """),
            {"u": username, "e": email}
        ).first()

        if existente:
            raise HTTPException(
                status_code=400,
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
        """
        Cambia la contraseña de un usuario existente.
        Siempre guarda el hash en bcrypt.
        Solo debería usarse desde un endpoint protegido por rol "admin".
        """
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
                status_code=404,
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
