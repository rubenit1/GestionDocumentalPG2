from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.hash import bcrypt
from jose import jwt, JWTError
from typing import List # <--- Mantenemos List, quitamos tuple

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
)
# Importamos los nuevos modelos Pydantic
from app.models.usuario import UserPublic, UserInDB, TokenData, UserCreateRequest, UserUpdateRequest, PasswordResetRequest

class AuthService:

    def _translate_to_public(self, user_in_db: dict) -> UserPublic:
        """
        Traduce un diccionario de la BD (con nombre_completo) 
        a un modelo UserPublic (con nombre).
        """
        if not user_in_db:
            return None
            
        # Copia para no modificar el original
        user_data = dict(user_in_db) 
        
        # La traducción clave
        if 'nombre_completo' in user_data:
            user_data['nombre'] = user_data.pop('nombre_completo')
        
        # Asumiendo Pydantic v1. Si es v2, usa: UserPublic.model_validate(user_data)
        return UserPublic.parse_obj(user_data) 

    def _execute_sp_and_translate(self, db: Session, sp_name: str, params: dict) -> UserPublic:
        """Helper para ejecutar un SP CRUD y traducir la respuesta"""
        try:
            result = db.execute(text(sp_name), params).mappings().first()
            db.commit()
        except Exception as e:
            db.rollback()
            # Chequear error de duplicado
            if "UNIQUE KEY" in str(e) or "duplicate key" in str(e):
                raise HTTPException(status_code=400, detail="El usuario o email ya existe")
            raise HTTPException(status_code=500, detail=f"Error en SP: {str(e)}")

        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado o SP no devolvió resultado")
        
        return self._translate_to_public(result)

    def login(self, db: Session, login: str, password: str) -> tuple[str, UserPublic]: # <--- Sintaxis moderna (correcta para Py 3.11)
        """
        Autentica al usuario, devuelve (token, UserPublic).
        """
        if not JWT_SECRET or JWT_SECRET == "change_me":
            raise HTTPException(status_code=500, detail="JWT_SECRET no está configurado")

        # 1. Consultar el usuario en la BD (SP_Auth_Login)
        try:
            result = db.execute(
                text("EXEC dbo.sp_Auth_Login @login=:login"),
                {"login": login}
            ).mappings().first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en sp_Auth_Login: {str(e)}")

        if not result:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        if not result["is_active"]:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        # 2. Verificar bcrypt
        stored_hash = result["password_hash"] or ""
        try:
            if not bcrypt.verify(password, stored_hash):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
        except Exception:
             raise HTTPException(status_code=401, detail="Credenciales inválidas (hash error)")

        # 3. Traducir a modelo público
        user_public = self._translate_to_public(result)

        # 4. Generar token JWT
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
        payload = {
            "sub": str(user_public.id),
            "username": user_public.username,
            "rol": user_public.rol,
            "exp": expire,
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return token, user_public

    def decode_token(self, token: str) -> TokenData:
        """Valida el JWT y regresa los datos (TokenData)"""
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return TokenData(
                id=int(data["sub"]),
                username=data["username"],
                rol=data["rol"]
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")

    def crear_usuario(self, db: Session, user_data: UserCreateRequest) -> UserPublic:
        """Crea un usuario usando el SP"""
        password_hash = bcrypt.hash(user_data.password)
        
        sp_sql = """
            EXEC dbo.sp_Usuarios_CRUD
                @accion = 'CREATE',
                @username = :username,
                @email = :email,
                @nombre = :nombre,
                @password_hash = :password_hash,
                @rol = :rol
        """
        params = {
            "username": user_data.username,
            "email": user_data.email,
            "nombre": user_data.nombre, # El SP acepta 'nombre'
            "password_hash": password_hash,
            "rol": user_data.rol
        }
        
        return self._execute_sp_and_translate(db, sp_sql, params)

    def reset_password(self, db: Session, reset_data: PasswordResetRequest) -> UserPublic:
        """Resetea la contraseña de un usuario usando el SP"""
        nuevo_hash = bcrypt.hash(reset_data.new_password)
        
        sp_sql = """
            EXEC dbo.sp_Usuarios_CRUD
                @accion = 'UPDATE_PASSWORD',
                @id = :id,
                @password_hash = :ph
        """
        params = {
            "id": reset_data.user_id,
            "ph": nuevo_hash
        }
        
        return self._execute_sp_and_translate(db, sp_sql, params)

    def listar_usuarios(self, db: Session, todos: bool = False) -> List[UserPublic]: # <--- Usamos List (importado)
        """Lista usuarios activos o todos usando el SP"""
        accion = "LIST_ALL" if todos else "LIST"
        try:
            rows = db.execute(
                text("EXEC dbo.sp_Usuarios_CRUD @accion = :accion"),
                {"accion": accion}
            ).mappings().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {str(e)}")

        # Traducir cada item de la lista
        return [self._translate_to_public(row) for row in rows]

    def editar_usuario(self, db: Session, user_id: int, user_data: UserUpdateRequest) -> UserPublic:
        """Actualiza un usuario usando el SP"""
        sp_sql = """
            EXEC dbo.sp_Usuarios_CRUD
                @accion = 'UPDATE',
                @id = :id,
                @username = :username,
                @email = :email,
                @nombre = :nombre,
                @rol = :rol
        """
        params = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "nombre": user_data.nombre, # El SP acepta 'nombre'
            "rol": user_data.rol
        }
        
        return self._execute_sp_and_translate(db, sp_sql, params)

    def desactivar_usuario(self, db: Session, user_id: int) -> UserPublic:
        """Desactiva un usuario (borrado lógico) usando el SP"""
        sp_sql = "EXEC dbo.sp_Usuarios_CRUD @accion = 'DISABLE', @id = :id"
        params = {"id": user_id}
        
        return self._execute_sp_and_translate(db, sp_sql, params)

# Instancia única del servicio
auth_service = AuthService()

