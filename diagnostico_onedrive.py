# diagnostico_onedrive.py
"""
Script de diagnóstico para identificar problemas con OneDrive
Ejecutar: python diagnostico_onedrive.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

def main():
    print("\n" + "🔍 " + "="*66 + " 🔍")
    print("     DIAGNÓSTICO: INTEGRACIÓN ONEDRIVE")
    print("🔍 " + "="*66 + " 🔍\n")
    
    # ===== PASO 1: VERIFICAR CONFIGURACIÓN =====
    print("PASO 1: Verificando configuración...")
    print("-" * 70)
    
    try:
        from app.core.config import (
            AZURE_CLIENT_ID,
            AZURE_CLIENT_SECRET,
            AZURE_TENANT_ID,
            ONEDRIVE_USER_ID
        )
        
        print(f"✅ Configuración cargada:")
        print(f"   Client ID: {AZURE_CLIENT_ID[:20] if AZURE_CLIENT_ID else '❌ NO CONFIGURADO'}...")
        print(f"   Tenant ID: {AZURE_TENANT_ID[:20] if AZURE_TENANT_ID else '❌ NO CONFIGURADO'}...")
        print(f"   Usuario: {ONEDRIVE_USER_ID if ONEDRIVE_USER_ID else '❌ NO CONFIGURADO'}")
        print(f"   Secret: {'✅ Configurado' if AZURE_CLIENT_SECRET else '❌ NO CONFIGURADO'}")
        
        if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, ONEDRIVE_USER_ID]):
            print("\n❌ ERROR: Configuración incompleta")
            print("   Verifica que .env tenga todas las variables necesarias")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False
    
    # ===== PASO 2: VERIFICAR TOKEN =====
    print("\n\nPASO 2: Verificando autenticación con Azure AD...")
    print("-" * 70)
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        token = onedrive._obtener_token()
        
        print(f"✅ Token obtenido exitosamente")
        print(f"   Preview: {token[:30]}...")
        print(f"   Longitud: {len(token)} caracteres")
        
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        print("\n💡 Posibles causas:")
        print("   - Client ID o Secret incorrectos")
        print("   - Tenant ID incorrecto")
        print("   - Permisos no otorgados en Azure AD")
        return False
    
    # ===== PASO 3: VERIFICAR USUARIO EXISTE =====
    print("\n\nPASO 3: Verificando que el usuario existe...")
    print("-" * 70)
    
    try:
        import requests
        
        url = f"{onedrive.graph_url}/users/{onedrive.user_id}"
        response = requests.get(url, headers=onedrive._headers())
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Usuario encontrado:")
            print(f"   Nombre: {user.get('displayName', 'N/A')}")
            print(f"   Email: {user.get('mail', 'N/A')}")
            print(f"   UPN: {user.get('userPrincipalName', 'N/A')}")
            print(f"   Job Title: {user.get('jobTitle', 'N/A')}")
        else:
            print(f"❌ Usuario NO encontrado")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            print(f"\n💡 Verifica que ONEDRIVE_USER_ID sea correcto:")
            print(f"   Actual: {onedrive.user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando usuario: {e}")
        return False
    
    # ===== PASO 4: VERIFICAR ONEDRIVE =====
    print("\n\nPASO 4: Verificando OneDrive del usuario...")
    print("-" * 70)
    
    try:
        url = f"{onedrive.graph_url}/users/{onedrive.user_id}/drive"
        response = requests.get(url, headers=onedrive._headers())
        
        if response.status_code == 200:
            drive = response.json()
            print(f"✅ OneDrive encontrado:")
            print(f"   Nombre: {drive.get('name', 'N/A')}")
            print(f"   Tipo: {drive.get('driveType', 'N/A')}")
            print(f"   ID: {drive.get('id', 'N/A')[:30]}...")
            print(f"   Owner: {drive.get('owner', {}).get('user', {}).get('displayName', 'N/A')}")
            
            # Verificar cuota
            quota = drive.get('quota', {})
            if quota:
                total = quota.get('total', 0) / (1024**3)  # GB
                used = quota.get('used', 0) / (1024**3)  # GB
                remaining = quota.get('remaining', 0) / (1024**3)  # GB
                print(f"   Espacio total: {total:.2f} GB")
                print(f"   Usado: {used:.2f} GB")
                print(f"   Disponible: {remaining:.2f} GB")
            
        else:
            error_data = response.json().get('error', {})
            error_code = error_data.get('code', 'N/A')
            error_msg = error_data.get('message', 'N/A')
            
            print(f"❌ OneDrive NO encontrado")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error Code: {error_code}")
            print(f"   Mensaje: {error_msg}")
            
            if error_code == "ResourceNotFound" or "mysite not found" in error_msg:
                print(f"\n💡 SOLUCIÓN:")
                print(f"   El usuario NO ha inicializado su OneDrive")
                print(f"\n   Pasos a seguir:")
                print(f"   1. Ir a: https://www.office.com")
                print(f"   2. Iniciar sesión con: {onedrive.user_id}")
                print(f"   3. Hacer clic en OneDrive (arriba izquierda)")
                print(f"   4. Esperar a que OneDrive se inicialice")
                print(f"   5. Crear una carpeta de prueba")
                print(f"   6. Volver a ejecutar este script")
            else:
                print(f"\n💡 Posibles causas:")
                print(f"   - Usuario sin licencia de OneDrive")
                print(f"   - Permisos insuficientes de la app")
                print(f"   - Usuario bloqueado o inactivo")
            
            return False
            
    except Exception as e:
        print(f"❌ Error verificando OneDrive: {e}")
        return False
    
    # ===== PASO 5: VERIFICAR PERMISOS =====
    print("\n\nPASO 5: Verificando permisos de la aplicación...")
    print("-" * 70)
    
    try:
        # Intentar listar items del root
        url = f"{onedrive.graph_url}/users/{onedrive.user_id}/drive/root/children"
        response = requests.get(url, headers=onedrive._headers())
        
        if response.status_code == 200:
            items = response.json().get('value', [])
            print(f"✅ Permisos correctos - Se pueden listar archivos")
            print(f"   Items en root: {len(items)}")
            
            if items:
                print(f"\n   Primeros 3 items:")
                for item in items[:3]:
                    tipo = "📁" if 'folder' in item else "📄"
                    print(f"   {tipo} {item.get('name')}")
        else:
            print(f"⚠️ No se pueden listar archivos")
            print(f"   Status: {response.status_code}")
            print(f"   Puede que falten permisos en Azure AD")
            
    except Exception as e:
        print(f"⚠️ Error verificando permisos: {e}")
    
    # ===== RESUMEN =====
    print("\n\n" + "="*70)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*70)
    print("\nTodo está configurado correctamente.")
    print("Puedes ejecutar el script de pruebas completo:")
    print("  python test_onedrive_integration.py")
    print("\nO inicializar la estructura de carpetas:")
    print("  python inicializar_onedrive.py")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Diagnóstico cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
