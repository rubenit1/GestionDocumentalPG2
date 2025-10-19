# app/services/ocr.py
import re
from num2words import num2words

def parse_ocr_text(text: str):
    """
    Parser OCR optimizado para formato de tabla guatemalteco.
    """
    print("\n" + "="*70)
    print("📄 TEXTO EXTRAÍDO POR OCR:")
    print("="*70)
    print(text)
    print("="*70 + "\n")
    
    data = {}
    
    # Patrones de búsqueda más flexibles
    patterns = [
        # Empresa
        ('empresa_contratante', r"EMPRESA[:\s]+([^\n]+)"),
        
        # Colaborador
        ('nombre_completo', r"COLABORADOR[:\s]+([^\n]+)"),
        
        # DPI/CUI
        ('cui', r"DPI\s*[/J]?\s*PASAPORTE[:\s]+(\d+)"),
        ('cui', r"DPI[:\s]+(\d+)"),
        
        # Dirección
        ('direccion', r"DIRECCI[OÓ]N[:\s]+([^\n]+)"),
        
        # Fecha de Inicio
        ('fecha_inicio', r"FECHA\s+DE\s+INICIO[:\s]+([^\n]+)"),
        
        # Fecha de Finalización
        ('fecha_fin', r"FECHA\s+DE\s+FINALIZACI[OÓ]N[:\s]+([^\n]+)"),
        
        # Honorarios
        ('monto', r"HONORARIOS\s+POR\s+PA[GC]AR[:\s]+([\d,]+\.?\d{0,2})"),
        
        # Posición
        ('posicion', r"POSICI[OÓ]N[:\s]+([A-ZÁÉÍÓÚÑ\s]+?)(?:QUEDO|ATENTO|SALUDOS|$)"),
        
        # Profesión
        ('profesion', r"PROFESI[OÓ]N[:\s]+([^\n]+)"),
        
        # Estado Civil
        ('estado_civil', r"ESTADO\s+CIVIL[:\s]+([^\n]+)"),
        
        # EDAD - MEJORADO CON MÁS PATRONES
        ('edad', r"EDAD[:\s]+(\d+)"),
        ('edad', r"EDAD\s+(\d+)"),
        ('edad', r"(?:^|\n)EDAD\s*[:\s]*(\d+)"),
    ]
    
    # Extraer datos usando los patrones
    for key, pattern in patterns:
        if key not in data:  # Solo si no se ha encontrado antes
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Limpiar comas del monto
                if key == 'monto':
                    value = value.replace(',', '')
                data[key] = value
                print(f"✓ {key}: {value}")
    
    # Limpiar el campo posición
    if data.get('posicion'):
        posicion = data['posicion']
        for keyword in ['QUEDO', 'ATENTO', 'SALUDOS', 'CORDIALES']:
            if keyword in posicion.upper():
                posicion = posicion.split(keyword)[0].strip()
                break
        data['posicion'] = posicion
        print(f"✓ posicion (limpiada): {posicion}")
    
    # Procesar el monto
    monto_numero = 0.0
    monto_en_letras = "CERO QUETZALES EXACTOS"
    monto_formateado = "Q.0.00"
    
    if data.get("monto"):
        try:
            monto_numero = float(data["monto"])
            monto_formateado = f"Q.{monto_numero:,.2f}"
            parte_entera = int(monto_numero)
            monto_en_letras = num2words(parte_entera, lang='es').upper() + " QUETZALES EXACTOS"
            print(f"✓ monto procesado: {monto_formateado} ({monto_en_letras})")
        except (ValueError, TypeError) as e:
            print(f"⚠ Error al procesar monto: {e}")
    
    # Procesar fecha de fin
    fecha_fin_texto = data.get("fecha_fin")
    if not fecha_fin_texto or "indefinido" in fecha_fin_texto.lower():
        fecha_fin_texto = "Contrato Indefinido"
    
    # Construir la respuesta estructurada
    structured_data = {
        "empresa_contratante": data.get("empresa_contratante", ""),
        "datos_persona": {
            "cui": data.get("cui", ""),
            "nombre_completo": data.get("nombre_completo", ""),
            "direccion": data.get("direccion", ""),
            "edad": data.get("edad", ""),  # ← Ahora debería capturarse
            "estado_civil": data.get("estado_civil", ""),
            "profesion": data.get("profesion", ""),
            "posicion": data.get("posicion", "")
        },
        "datos_contrato": {
            "tipo_contrato": data.get("posicion", "Servicios Profesionales"),
            "fecha_inicio": data.get("fecha_inicio", ""),
            "fecha_fin": fecha_fin_texto,
            "monto": monto_formateado,
            "monto_en_letras": monto_en_letras,
            "descripcion_adicional": f"Posición: {data.get('posicion', 'N/A')}"
        }
    }
    
    print("\n" + "="*70)
    print("📋 RESULTADO PROCESADO:")
    print("="*70)
    import json
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))
    print("="*70 + "\n")
    
    return structured_data