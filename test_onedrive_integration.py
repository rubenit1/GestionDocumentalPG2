# test_onedrive_integration.py
"""
Script de prueba para validar la integración con OneDrive
Ejecutar: python test_onedrive_integration.py
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath('.'))

def test_1_configuracion():
    """Verifica que las variables de entorno estén configuradas"""
    print("\n" + "="*70)
    print("TEST 1: Verificación de Configuración")
    print("="*70)
    
    try:
        from app.core.config import verificar_configuracion
        azure_ok = verificar_configuracion()
        
        if azure_ok:
            print("✅ Configuración correcta")
            return True
        else:
            print("❌ Configuración incompleta - Revisa .env")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False


def test_2_conexion_azure():
    """Prueba la conexión con Azure AD y verifica OneDrive"""
    print("\n" + "="*70)
    print("TEST 2: Conexión con Azure AD y OneDrive")
    print("="*70)
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Obtener token
        token = onedrive._obtener_token()
        
        if token:
            print(f"✅ Token obtenido exitosamente")
            print(f"   Preview: {token[:30]}...")
        else:
            print("❌ No se pudo obtener token")
            return False
        
        # Verificar que OneDrive esté inicializado
        print("\n🔍 Verificando OneDrive del usuario...")
        onedrive_ok = onedrive.verificar_onedrive_inicializado()
        
        if not onedrive_ok:
            print("\n⚠️ IMPORTANTE:")
            print("   El usuario debe acceder a OneDrive al menos una vez")
            print("   Para inicializar:")
            print("   1. Ir a https://onedrive.live.com")
            print("   2. Iniciar sesión con el usuario configurado")
            print("   3. Esperar que OneDrive se inicialice completamente")
            return False
        
        return True
            
    except Exception as e:
        print(f"❌ Error conectando a Azure: {e}")
        return False


def test_3_crear_carpeta():
    """Prueba crear una carpeta en OneDrive"""
    print("\n" + "="*70)
    print("TEST 3: Crear Carpeta de Prueba")
    print("="*70)
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Intentar crear carpeta de prueba
        result = onedrive.crear_carpeta(
            parent_path="/",
            folder_name="Documentos_Legales_TEST"
        )
        
        print(f"✅ Carpeta creada exitosamente")
        print(f"   ID: {result['id']}")
        print(f"   Nombre: {result['name']}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando carpeta: {e}")
        return False


def test_4_subir_archivo():
    """Prueba subir un archivo de prueba"""
    print("\n" + "="*70)
    print("TEST 4: Subir Archivo de Prueba")
    print("="*70)
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Crear archivo de prueba
        test_content = b"Este es un archivo de prueba para validar OneDrive"
        test_filename = "test_documento.txt"
        test_path = f"/Documentos_Legales_TEST/{test_filename}"
        
        # Subir archivo
        result = onedrive.subir_archivo(
            file_path=test_filename,
            onedrive_path=test_path,
            file_content=test_content
        )
        
        print(f"✅ Archivo subido exitosamente")
        print(f"   ID: {result['id']}")
        print(f"   Nombre: {result['name']}")
        print(f"   Tamaño: {result['size']} bytes")
        
        return result['id']
        
    except Exception as e:
        print(f"❌ Error subiendo archivo: {e}")
        return None


def test_5_descargar_archivo(file_id):
    """Prueba descargar el archivo subido"""
    print("\n" + "="*70)
    print("TEST 5: Descargar Archivo")
    print("="*70)
    
    if not file_id:
        print("⚠️ Saltando test - no hay file_id del test anterior")
        return False
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Descargar archivo
        content = onedrive.descargar_archivo(file_id)
        
        print(f"✅ Archivo descargado exitosamente")
        print(f"   Contenido: {content.decode()[:50]}...")
        print(f"   Tamaño: {len(content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error descargando archivo: {e}")
        return False


def test_6_link_compartido(file_id):
    """Prueba generar link compartido"""
    print("\n" + "="*70)
    print("TEST 6: Generar Link Compartido")
    print("="*70)
    
    if not file_id:
        print("⚠️ Saltando test - no hay file_id del test anterior")
        return False
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Generar link
        link = onedrive.obtener_link_compartido(file_id, tipo="view")
        
        print(f"✅ Link generado exitosamente")
        print(f"   URL: {link}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando link: {e}")
        return False


def test_7_buscar_archivo():
    """Prueba buscar archivos"""
    print("\n" + "="*70)
    print("TEST 7: Buscar Archivos")
    print("="*70)
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        onedrive = OneDriveService()
        
        # Buscar archivos de prueba
        resultados = onedrive.buscar_archivos("test_documento")
        
        print(f"✅ Búsqueda exitosa")
        print(f"   Archivos encontrados: {len(resultados)}")
        
        if resultados:
            for item in resultados[:3]:  # Mostrar primeros 3
                print(f"   - {item['name']} (ID: {item['id'][:20]}...)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error buscando archivos: {e}")
        return False


def ejecutar_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "🧪 " + "="*66 + " 🧪")
    print("     SUITE DE PRUEBAS: INTEGRACIÓN ONEDRIVE API")
    print("🧪 " + "="*66 + " 🧪")
    
    resultados = []
    file_id = None
    
    # Test 1: Configuración
    resultados.append(("Configuración", test_1_configuracion()))
    
    if not resultados[0][1]:
        print("\n⚠️ Configuración incorrecta - Deteniendo tests")
        print("   Configura .env con las credenciales de Azure AD")
        return
    
    # Test 2: Conexión Azure
    resultados.append(("Conexión Azure AD", test_2_conexion_azure()))
    
    if not resultados[1][1]:
        print("\n⚠️ No se pudo conectar a Azure - Deteniendo tests")
        return
    
    # Test 3: Crear carpeta
    resultados.append(("Crear Carpeta", test_3_crear_carpeta()))
    
    # Test 4: Subir archivo
    file_id = test_4_subir_archivo()
    resultados.append(("Subir Archivo", file_id is not None))
    
    # Test 5: Descargar archivo
    resultados.append(("Descargar Archivo", test_5_descargar_archivo(file_id)))
    
    # Test 6: Link compartido
    resultados.append(("Link Compartido", test_6_link_compartido(file_id)))
    
    # Test 7: Buscar archivos
    resultados.append(("Buscar Archivos", test_7_buscar_archivo()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)
    
    exitosos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        emoji = "✅" if resultado else "❌"
        print(f"{emoji} {nombre}")
    
    print("\n" + "-"*70)
    print(f"Exitosos: {exitosos}/{total} ({exitosos/total*100:.0f}%)")
    print("="*70 + "\n")
    
    if exitosos == total:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        print("   La integración con OneDrive está funcionando correctamente")
    elif exitosos > 0:
        print("⚠️ Algunos tests fallaron")
        print("   Revisa los errores anteriores y la documentación")
    else:
        print("❌ Todos los tests fallaron")
        print("   Verifica la configuración en .env y Azure Portal")


if __name__ == "__main__":
    ejecutar_tests()
