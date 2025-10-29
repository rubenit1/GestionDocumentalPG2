from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.hash import bcrypt
from jose import jwt

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
)

class AuthService:
    def _actualizar_hash_en_bd(self, db: Session, user_id: int, new_hash: str):
        # Guardamos el nuevo hash seguro en la BD
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
        # 1. Traer usuario usando SP
        result = db.execute(
            text("EXEC dbo.sp_Auth_Login @login=:login"),
            {"login": login}
        ).mappings().first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )

        if not result["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )

        user_id = result["id"]
        stored_value = result["password_hash"]

        # 2. Intento #1: verificar como bcrypt
        password_ok = False
        is_bcrypt = False

        if stored_value and str(stored_value).startswith(("$2a$", "$2b$", "$2y$")):
            # Ya es hash bcrypt
            is_bcrypt = True
            if bcrypt.verify(password, stored_value):
                password_ok = True

        # 3. Intento #2 (fallback): comparar directo el texto plano
        #    SOLO si no era bcrypt
        if not password_ok and not is_bcrypt:
            if password == stored_value:
                password_ok = True
                # Migrar inmediatamente a bcrypt.hash(...)
                nuevo_hash = bcrypt.hash(password)
                self._actualizar_hash_en_bd(db, user_id, nuevo_hash)

        if not password_ok:
            # Ninguna validación pasó
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        # 4. Generar token JWT
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
        payload = {
            "sub": str(result["id"]),
            "username": result["username"],
            "rol": result["rol"],
            "exp": expire,
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

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
        from jose import JWTError
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
        """
        Alta de usuario (solo para admins). Siempre guarda hash bcrypt.
        Devuelve el usuario creado.
        """
        # 1. Validar que no exista el username/email
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

        # 2. Hash de la contraseña
        hashed = bcrypt.hash(password_plano)

        # 3. Insert
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
        Resetea la contraseña de un usuario dado. Siempre reescribe con hash bcrypt.
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
