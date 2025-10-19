#!/usr/bin/env python3
"""
Script de prueba para verificar la implementación de docxtpl
Ejecutar: python test_docxtpl.py
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_imports():
    """Prueba 1: Verificar que todas las librerías están instaladas"""
    print("\n" + "="*70)
    print("PRUEBA 1: Verificando importaciones...")
    print("="*70)
    
    try:
        import docxtpl
        print("✅ docxtpl instalado correctamente")
        print(f"   Versión: {docxtpl.__version__}")
    except ImportError:
        print("❌ ERROR: docxtpl no está instalado")
        print("   Ejecuta: pip install docxtpl")
        return False
    
    try:
        from docx import Document
        print("✅ python-docx instalado correctamente")
    except ImportError:
        print("❌ ERROR: python-docx no está instalado")
        return False
    
    try:
        from num2words import num2words
        print("✅ num2words instalado correctamente")
    except ImportError:
        print("❌ ERROR: num2words no está instalado")
        return False
    
    try:
        from fastapi import FastAPI
        print("✅ FastAPI instalado correctamente")
    except ImportError:
        print("❌ ERROR: FastAPI no está instalado")
        return False
    
    return True


def test_service_import():
    """Prueba 2: Verificar que el servicio V2 se puede importar"""
    print("\n" + "="*70)
    print("PRUEBA 2: Verificando servicio documento_v2...")
    print("="*70)
    
    try:
        from app.services.documento_v2 import ServicioDocumentoV2
        print("✅ ServicioDocumentoV2 importado correctamente")
        
        servicio = ServicioDocumentoV2()
        print("✅ Servicio instanciado correctamente")
        return True
    except Exception as e:
        print(f"❌ ERROR al importar servicio: {str(e)}")
        return False


def test_template_folder():
    """Prueba 3: Verificar que existe la carpeta de plantillas"""
    print("\n" + "="*70)
    print("PRUEBA 3: Verificando carpeta templates...")
    print("="*70)
    
    if os.path.exists("templates"):
        print("✅ Carpeta templates/ existe")
        
        # Listar plantillas
        templates = [f for f in os.listdir("templates") if f.endswith('.docx')]
        print(f"   Plantillas encontradas: {len(templates)}")
        for t in templates:
            print(f"   - {t}")
        return True
    else:
        print("⚠️  Carpeta templates/ no existe")
        print("   Creando carpeta...")
        os.makedirs("templates")
        print("✅ Carpeta creada")
        return True


def test_simple_context():
    """Prueba 4: Verificar preparación de contexto"""
    print("\n" + "="*70)
    print("PRUEBA 4: Verificando preparación de contexto...")
    print("="*70)
    
    try:
        from app.services.documento_v2 import ServicioDocumentoV2
        import datetime
        
        servicio = ServicioDocumentoV2()
        
        # Datos de prueba
        empresa_mock = {
            'razon_social': 'TEST S.A.',
            'numero_registro': '12345',
            'numero_folio': '100',
            'numero_libro': '50',
            'autorizada_en': 'Guatemala',
            'fecha_autorizacion': datetime.date(2020, 1, 15),
            'autorizada_por': 'Notario Test',
            'inscrita_en': 'Registro Mercantil',
            'tipo_libro': 'Sociedades',
            'lugar_notificaciones': 'Zona 10, Guatemala',
            'segundo_lugar_notificaciones': 'Zona 15, Guatemala',
        }
        
        representante_mock = {
            'nombre_completo': 'Juan Pérez',
            'cui': '1234567890101',
            'fecha_nacimiento': datetime.date(1980, 5, 10),
            'estado_civil': 'Casado',
            'profesion': 'Ingeniero',
            'nacionalidad': 'Guatemalteco',
            'extendido_en': 'Guatemala',
        }
        
        # Crear mock de solicitud
        from app.models.documento import GenerationRequest, DocumentoProcesado, PersonaData, ContratoData
        
        solicitud_mock = type('obj', (object,), {
            'template_name': 'test.docx',
            'empresa_id': 1,
            'representante_id': 1,
            'fecha_contrato': '2025-01-15',
            'colaborador_data': DocumentoProcesado(
                empresa_contratante='TEST S.A.',
                datos_persona=PersonaData(
                    nombre_completo='Mario Miranda',
                    cui='9876543210101',
                    edad='30',
                    direccion='Zona 1, Guatemala',
                    estado_civil='Soltero',
                    profesion='Contador',
                    nacionalidad='Guatemalteco',
                    posicion='Supervisor'
                ),
                datos_contrato=ContratoData(
                    fecha_inicio='2025-01-15',
                    fecha_fin='Por tiempo indefinido',
                    monto='Q.5,000.00',
                    monto_en_letras='CINCO MIL QUETZALES EXACTOS',
                    tipo_contrato='Tiempo Indefinido'
                )
            )
        })()
        
        context = servicio._preparar_contexto(empresa_mock, representante_mock, solicitud_mock)
        
        print("✅ Contexto preparado correctamente")
        print(f"   Secciones: {list(context.keys())}")
        print(f"   Colaborador: {context['colaborador']['nombre_completo']}")
        print(f"   Empresa: {context['empresa']['razon_social']}")
        print(f"   Representante: {context['representante']['nombre_completo']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint():
    """Prueba 5: Verificar que el endpoint está registrado"""
    print("\n" + "="*70)
    print("PRUEBA 5: Verificando endpoint /documentos-v2...")
    print("="*70)
    
    try:
        from app.api.v1.api import api_router
        
        routes = [route.path for route in api_router.routes]
        
        if '/documentos-v2/generate' in routes:
            print("✅ Endpoint /documentos-v2/generate registrado")
        else:
            print("⚠️  Endpoint no encontrado en las rutas")
            print(f"   Rutas disponibles: {routes}")
        
        if '/documentos-v2/ocr' in routes:
            print("✅ Endpoint /documentos-v2/ocr registrado")
        
        if '/documentos-v2/test' in routes:
            print("✅ Endpoint /documentos-v2/test registrado")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "🧪 "*20)
    print("INICIANDO PRUEBAS DE IMPLEMENTACIÓN DOCXTPL")
    print("🧪 "*20)
    
    results = []
    
    results.append(("Importaciones", test_imports()))
    results.append(("Servicio V2", test_service_import()))
    results.append(("Carpeta templates", test_template_folder()))
    results.append(("Contexto", test_simple_context()))
    results.append(("Endpoints", test_endpoint()))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {name}")
    
    print("\n" + "="*70)
    print(f"Resultado: {passed}/{total} pruebas exitosas")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("\nPróximos pasos:")
        print("1. Inicia el backend: uvicorn app.main:app --reload")
        print("2. Actualiza una plantilla Word con sintaxis de docxtpl")
        print("3. Prueba generando un documento")
        print("\nVer README_IMPLEMENTACION.md para más detalles")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\nSugerencias:")
        print("1. Instala dependencias faltantes: pip install -r requirements.txt")
        print("2. Verifica que todos los archivos se crearon correctamente")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
