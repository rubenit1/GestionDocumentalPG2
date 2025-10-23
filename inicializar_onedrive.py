# inicializar_onedrive.py
"""
Script para inicializar la estructura de carpetas en OneDrive
Ejecutar: python inicializar_onedrive.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

def main():
    print("\n" + "📁 " + "="*66 + " 📁")
    print("     INICIALIZACIÓN: ESTRUCTURA DE CARPETAS ONEDRIVE")
    print("📁 " + "="*66 + " 📁\n")
    
    try:
        from app.services.onedrive_service import OneDriveService
        
        # Crear servicio
        onedrive = OneDriveService()
        
        # Verificar que OneDrive esté accesible
        print("🔍 Verificando acceso a OneDrive...")
        if not onedrive.verificar_onedrive_inicializado():
            print("\n❌ No se puede acceder a OneDrive")
            print("   Ejecuta primero: python diagnostico_onedrive.py")
            return False
        
        print("\n📁 Creando estructura de carpetas...")
        print("-" * 70)
        
        # Crear carpetas usando el método del servicio
        carpetas = onedrive.inicializar_estructura_carpetas()
        
        print("\n" + "="*70)
        print("✅ ESTRUCTURA CREADA EXITOSAMENTE")
        print("="*70)
        
        print("\n📊 Resumen de carpetas creadas:")
        print("-" * 70)
        
        estructura = {
            "Documentos_Legales": [
                "├── Contratos",
                "├── Minutas",
                "├── Anexos",
                "├── Cartas",
                "├── Imagenes_Originales",
                "├── Plantillas",
                "└── Temp"
            ]
        }
        
        for raiz, subcarpetas in estructura.items():
            print(f"\n📁 {raiz}/")
            for carpeta in subcarpetas:
                print(f"   {carpeta}")
        
        print("\n" + "="*70)
        print("\n✅ Todo listo para usar el sistema")
        print("\nPróximos pasos:")
        print("  1. Ejecutar pruebas: python test_onedrive_integration.py")
        print("  2. Iniciar API: uvicorn app.main:app --reload")
        print("  3. Probar endpoint: POST /api/v1/flujo/procesar-y-generar")
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error inicializando carpetas: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Inicialización cancelada por el usuario")
        sys.exit(1)
