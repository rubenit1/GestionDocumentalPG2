# app/services/onedrive_service.py
"""
Servicio para integración con OneDrive usando Microsoft Graph API
VERSIÓN CORREGIDA - Usa Application Permissions correctamente

Requiere: pip install msal requests
"""

import os
import hashlib
import requests
from typing import Optional, Dict
from msal import ConfidentialClientApplication

class OneDriveService:
    """
    Servicio para interactuar con OneDrive Business usando Microsoft Graph API
    Usa Application Permissions (no Delegated)
    """
    
    def __init__(self):
        # Importar configuración centralizada
        from app.core.config import (
            AZURE_CLIENT_ID, 
            AZURE_CLIENT_SECRET, 
            AZURE_TENANT_ID, 
            ONEDRIVE_USER_ID
        )
        
        self.client_id = AZURE_CLIENT_ID
        self.client_secret = AZURE_CLIENT_SECRET
        self.tenant_id = AZURE_TENANT_ID
        self.user_id = ONEDRIVE_USER_ID
        
        # Configurar MSAL
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        # URL base de Graph API
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
    def _obtener_token(self) -> str:
        """Obtiene token de acceso de Azure AD usando Application Permissions"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Error obteniendo token: {result.get('error_description')}")
    
    def _headers(self) -> Dict[str, str]:
        """Headers con autenticación"""
        return {
            "Authorization": f"Bearer {self._obtener_token()}",
            "Content-Type": "application/json"
        }
    
    def verificar_onedrive_inicializado(self) -> bool:
        """
        Verifica si el usuario tiene OneDrive inicializado
        IMPORTANTE: El usuario debe haber accedido a OneDrive al menos una vez
        """
        try:
            url = f"{self.graph_url}/users/{self.user_id}/drive"
            response = requests.get(url, headers=self._headers())
            
            if response.status_code == 200:
                drive_info = response.json()
                print(f"✅ OneDrive encontrado: {drive_info.get('name', 'N/A')}")
                return True
            else:
                print(f"❌ OneDrive no inicializado o usuario sin acceso: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error verificando OneDrive: {e}")
            return False
    
    def subir_archivo(
        self, 
        file_path: str, 
        onedrive_path: str,
        file_content: Optional[bytes] = None
    ) -> Dict:
        """
        Sube un archivo a OneDrive del usuario especificado
        
        Args:
            file_path: Ruta local del archivo O nombre del archivo
            onedrive_path: Ruta en OneDrive (ej: /Documentos_Legales/Contratos/contrato.docx)
            file_content: Contenido del archivo en bytes (opcional si ya existe en file_path)
        
        Returns:
            Dict con información del archivo subido (id, webUrl, etc)
        """
        if file_content is None:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        
        # Codificar ruta para URL
        import urllib.parse
        encoded_path = urllib.parse.quote(onedrive_path)
        
        # Usar upload session para archivos grandes (>4MB) o simple PUT para pequeños
        file_size = len(file_content)
        
        if file_size < 4 * 1024 * 1024:  # Menor a 4MB
            return self._subir_simple(encoded_path, file_content)
        else:
            return self._subir_sesion(encoded_path, file_content)
    
    def _subir_simple(self, encoded_path: str, file_content: bytes) -> Dict:
        """Subida simple para archivos pequeños (<4MB)"""
        # Usar /users/{user_id}/drive para Application Permissions
        url = f"{self.graph_url}/users/{self.user_id}/drive/root:{encoded_path}:/content"
        
        headers = {
            "Authorization": f"Bearer {self._obtener_token()}",
            "Content-Type": "application/octet-stream"
        }
        
        response = requests.put(url, headers=headers, data=file_content)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_detail = response.text
            raise Exception(f"Error subiendo archivo: {response.status_code} - {error_detail}")
    
    def _subir_sesion(self, encoded_path: str, file_content: bytes) -> Dict:
        """Subida por sesión para archivos grandes (>4MB)"""
        # Crear sesión de subida
        url = f"{self.graph_url}/users/{self.user_id}/drive/root:{encoded_path}:/createUploadSession"
        
        response = requests.post(url, headers=self._headers())
        
        if response.status_code != 200:
            raise Exception(f"Error creando sesión: {response.status_code} - {response.text}")
        
        upload_url = response.json()["uploadUrl"]
        
        # Subir por fragmentos de 5MB
        chunk_size = 5 * 1024 * 1024
        file_size = len(file_content)
        
        for i in range(0, file_size, chunk_size):
            chunk = file_content[i:i + chunk_size]
            start = i
            end = min(i + chunk_size - 1, file_size - 1)
            
            headers = {
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end}/{file_size}"
            }
            
            response = requests.put(upload_url, headers=headers, data=chunk)
            
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"Error subiendo fragmento: {response.status_code}")
        
        return response.json()
    
    def descargar_archivo(self, file_id: str) -> bytes:
        """
        Descarga un archivo desde OneDrive por su ID
        
        Args:
            file_id: ID del archivo en OneDrive
        
        Returns:
            Contenido del archivo en bytes
        """
        url = f"{self.graph_url}/users/{self.user_id}/drive/items/{file_id}/content"
        
        response = requests.get(url, headers={"Authorization": f"Bearer {self._obtener_token()}"})
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Error descargando archivo: {response.status_code}")
    
    def obtener_info_archivo(self, file_id: str) -> Dict:
        """Obtiene información de un archivo"""
        url = f"{self.graph_url}/users/{self.user_id}/drive/items/{file_id}"
        
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error obteniendo info: {response.status_code}")
    
    def eliminar_archivo(self, file_id: str) -> bool:
        """Elimina un archivo de OneDrive"""
        url = f"{self.graph_url}/users/{self.user_id}/drive/items/{file_id}"
        
        response = requests.delete(url, headers=self._headers())
        
        return response.status_code == 204
    
    def crear_carpeta(self, parent_path: str, folder_name: str) -> Dict:
        """
        Crea una carpeta en OneDrive
        
        Args:
            parent_path: Ruta de la carpeta padre (ej: /Documentos_Legales)
            folder_name: Nombre de la nueva carpeta
        
        Returns:
            Dict con información de la carpeta creada
        """
        import urllib.parse
        
        # Si parent_path es "/", usar root directamente
        if parent_path == "/" or parent_path == "":
            url = f"{self.graph_url}/users/{self.user_id}/drive/root/children"
        else:
            encoded_path = urllib.parse.quote(parent_path)
            url = f"{self.graph_url}/users/{self.user_id}/drive/root:{encoded_path}:/children"
        
        body = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        response = requests.post(url, headers=self._headers(), json=body)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error creando carpeta: {response.status_code} - {response.text}")
    
    def obtener_link_compartido(self, file_id: str, tipo: str = "view") -> str:
        """
        Crea un link compartido para un archivo
        
        Args:
            file_id: ID del archivo
            tipo: 'view' (solo ver) o 'edit' (editar)
        
        Returns:
            URL del link compartido
        """
        url = f"{self.graph_url}/users/{self.user_id}/drive/items/{file_id}/createLink"
        
        body = {
            "type": tipo,
            "scope": "organization"  # Solo usuarios de la organización
        }
        
        response = requests.post(url, headers=self._headers(), json=body)
        
        if response.status_code in [200, 201]:
            return response.json()["link"]["webUrl"]
        else:
            raise Exception(f"Error creando link: {response.status_code} - {response.text}")
    
    @staticmethod
    def calcular_hash(file_content: bytes) -> str:
        """Calcula SHA256 hash de un archivo"""
        return hashlib.sha256(file_content).hexdigest()
    
    def buscar_archivos(self, query: str) -> list:
        """
        Busca archivos en OneDrive
        
        Args:
            query: Término de búsqueda
        
        Returns:
            Lista de archivos encontrados
        """
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        url = f"{self.graph_url}/users/{self.user_id}/drive/root/search(q='{encoded_query}')"
        
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise Exception(f"Error buscando: {response.status_code} - {response.text}")
    
    def inicializar_estructura_carpetas(self) -> Dict[str, str]:
        """
        Crea la estructura de carpetas necesaria para el sistema
        Retorna un diccionario con las carpetas creadas y sus IDs
        """
        from app.core.config import ONEDRIVE_PATHS
        
        carpetas_creadas = {}
        
        print("\n📁 Inicializando estructura de carpetas en OneDrive...")
        
        # Crear carpeta raíz
        try:
            root_folder = self.crear_carpeta("/", "Documentos_Legales")
            carpetas_creadas["root"] = root_folder["id"]
            print(f"✅ Carpeta raíz creada: {root_folder['name']}")
        except Exception as e:
            print(f"⚠️ Carpeta raíz ya existe o error: {e}")
        
        # Crear subcarpetas
        subcarpetas = [
            "Contratos",
            "Minutas",
            "Anexos",
            "Cartas",
            "Imagenes_Originales",
            "Plantillas",
            "Temp"
        ]
        
        for carpeta in subcarpetas:
            try:
                resultado = self.crear_carpeta("/Documentos_Legales", carpeta)
                carpetas_creadas[carpeta.lower()] = resultado["id"]
                print(f"✅ Carpeta creada: {carpeta}")
            except Exception as e:
                print(f"⚠️ {carpeta} ya existe o error: {e}")
        
        return carpetas_creadas