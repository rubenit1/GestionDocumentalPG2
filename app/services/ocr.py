# app/services/ocr.py
import re
from num2words import num2words

def limpiar_fecha_gt(fecha_raw):
    """
    Limpia fechas mal formateadas por OCR.
    Formato guatemalteco: dd/mm/aaaa (día/mes/año)
    """
    if not fecha_raw:
        return fecha_raw
    
    fecha = str(fecha_raw).strip()
    
    # PRIMERO: Corregir caracteres mal leídos por OCR
    fecha = fecha.replace('h', '1').replace('H', '1')
    fecha = fecha.replace('o', '0').replace('O', '0')
    
    # Si ya tiene formato correcto dd/mm/aaaa, retornar
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', fecha):
        return fecha
    
    # Si solo tiene números sin separadores (ej: 13102025)
    if re.match(r'^\d{8}$', fecha):
        dia = fecha[:2]
        mes = fecha[2:4]
        anio = fecha[4:]
        return f"{dia}/{mes}/{anio}"
    
    # Si tiene formato parcial sin / entre día y mes (ej: 1310/2025 o 120/2026)
    match = re.match(r'^(\d{3,4})/(\d{4})$', fecha)
    if match:
        sin_anio = match.group(1)
        anio = match.group(2)
        
        if len(sin_anio) == 4:  # ej: 1310 -> 13/10
            dia = sin_anio[:2]
            mes = sin_anio[2:]
        elif len(sin_anio) == 3:  # ej: 120 -> 12/10
            dia = sin_anio[:2]
            mes = sin_anio[2:]
            # Si mes es 0, probablemente es 10
            if mes == '0':
                mes = '10'
        else:
            return fecha
        
        return f"{dia}/{mes}/{anio}"
    
    return fecha


def parse_ocr_text(text: str):
    """
    Parser OCR optimizado para formato de tabla guatemalteco.
    Versión mejorada con correcciones de caracteres OCR comunes.
    """
    print("\n" + "="*70)
    print(" TEXTO EXTRAÍDO POR OCR:")
    print("="*70)
    print(text)
    print("="*70 + "\n")
    
    data = {}
    
    # PRE-PROCESAMIENTO: Limpiar caracteres confusos comunes de OCR
    text_cleaned = text
    
    # Correcciones para EDAD
    text_cleaned = re.sub(r'EDAD[\s:]*S7', 'EDAD 57', text_cleaned, flags=re.IGNORECASE)
    text_cleaned = re.sub(r'EDAD[\s:]*s7', 'EDAD 57', text_cleaned, flags=re.IGNORECASE)
    text_cleaned = re.sub(r'\bS7\b', '57', text_cleaned)
    text_cleaned = re.sub(r'\bs7\b', '57', text_cleaned)
    text_cleaned = re.sub(r'EDAD[\s:]*S(\d)', r'EDAD 5\1', text_cleaned, flags=re.IGNORECASE)
    
    # Patrones de búsqueda
    patterns = [
        # Empresa
        ('empresa_contratante', r"EMPRESA[:\s]+([^\n]+)"),
        
        # Colaborador
        ('nombre_completo', r"COLABORADOR[:\s]+([^\n]+)"),
        
        # DPI/CUI - captura todo incluyendo espacios
        ('cui', r"DPI\s*[/]?\s*PASAPORTE[:\s]*([\d\s]+)"),
        ('cui', r"DPI[:\s]*([\d\s]+)"),
        
        # Dirección
        ('direccion', r"DIRECCI[OÓ]N[:\s]+([^\n]+)"),
        
        # Fecha de Inicio - captura formato dd/mm/aaaa o mal formateado
        ('fecha_inicio', r"FECHA\s+DE\s+INICIO[:\s]*(\d{1,2}/\d{1,2}/\d{4})"),
        ('fecha_inicio', r"FECHA\s+DE\s+INICIO[:\s]*([\d/hHoO]+)"),
        
        # Fecha de Finalización
        ('fecha_fin', r"FECHA\s+DE\s+FINALIZACI[OÓ]N[:\s]*(\d{1,2}/\d{1,2}/\d{4})"),
        ('fecha_fin', r"FECHA\s+DE\s+FINALIZACI[OÓ]N[:\s]*([\d/hHoO]+)"),
        ('fecha_fin', r"FECHA\s+DE\s+FINALIZACI[OÓ]N[:\s]+([^\n]+)"),
        
        # Honorarios - captura Q al inicio
        ('monto', r"HONORARIOS\s+POR\s+PA[GC]AR[:\s]*Q?([\d,\.]+)"),
        
        # Posición
        ('posicion', r"POSICI[OÓ]N[:\s]+([^\n]+)"),
        
        # Profesión
        ('profesion', r"PROFESI[OÓ]N[:\s]+([^\n]+)"),
        
        # Estado Civil
        ('estado_civil', r"ESTADO\s+CIVIL[:\s]+([^\n]+)"),
        
        # Edad
        ('edad', r"EDAD[:\s]*(\d{1,3})\s*a[ñn]os"),
        ('edad', r"EDAD[:\s]*(\d{1,3})"),
        ('edad', r"(\d{1,3})\s*a[ñn]os"),
    ]
    
    # Extraer datos usando los patrones
    for key, pattern in patterns:
        if key not in data:
            match = re.search(pattern, text_cleaned, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match:
                try:
                    value = match.group(1).strip()
                    if value:
                        data[key] = value
                        print(f"✓ {key}: {value}")
                except (ValueError, IndexError) as e:
                    print(f" Error procesando {key}: {e}")
    
    # ===== LIMPIEZA DE DATOS POST-EXTRACCIÓN =====
    
    # Limpiar CUI (quitar espacios)
    if data.get('cui'):
        data['cui'] = data['cui'].replace(' ', '').strip()
        print(f"✓ cui (limpiado): {data['cui']}")
    
    # Limpiar fechas con formato guatemalteco
    if data.get('fecha_inicio'):
        data['fecha_inicio'] = limpiar_fecha_gt(data['fecha_inicio'])
        print(f"✓ fecha_inicio (limpiada): {data['fecha_inicio']}")
    
    if data.get('fecha_fin'):
        fecha_fin = data['fecha_fin']
        # Verificar si es texto como "indefinido" o fecha
        if not any(palabra in fecha_fin.lower() for palabra in ['indefinido', 'tiempo']):
            data['fecha_fin'] = limpiar_fecha_gt(fecha_fin)
        print(f"✓ fecha_fin (limpiada): {data['fecha_fin']}")
    
    # Limpiar nombre (correcciones OCR comunes)
    if data.get('nombre_completo'):
        nombre = data['nombre_completo']
        nombre = re.sub(r'^L/', 'J', nombre)
        nombre = re.sub(r'\bL/', 'J', nombre)
        nombre = nombre.replace('0s', 'OS')
        nombre = nombre.replace('CRLOS', 'CARLOS')
        nombre = re.sub(r'\b0\b', 'O', nombre)
        data['nombre_completo'] = nombre.strip()
        print(f"✓ nombre_completo (limpiado): {data['nombre_completo']}")
    
    # Limpiar monto
    if data.get('monto'):
        monto = data['monto'].replace(',', '')
        data['monto'] = monto
        print(f"✓ monto (limpiado): {monto}")
    
    # Limpiar el campo posición
    if data.get('posicion'):
        posicion = data['posicion']
        for keyword in ['QUEDO', 'ATENTO', 'SALUDOS', 'CORDIALES']:
            if keyword in posicion.upper():
                posicion = posicion.split(keyword)[0].strip()
                break
        data['posicion'] = posicion
        print(f"✓ posicion (limpiada): {posicion}")
    
    # Validar edad
    if data.get('edad'):
        try:
            edad_num = int(data['edad'])
            if edad_num < 18 or edad_num > 99:
                data['edad'] = ""
        except:
            data['edad'] = ""
    
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
    if not fecha_fin_texto or "indefinido" in str(fecha_fin_texto).lower():
        fecha_fin_texto = "Contrato Indefinido"
    
    # Construir la respuesta estructurada
    structured_data = {
        "empresa_contratante": data.get("empresa_contratante", ""),
        "datos_persona": {
            "cui": data.get("cui", ""),
            "nombre_completo": data.get("nombre_completo", ""),
            "direccion": data.get("direccion", ""),
            "edad": data.get("edad", ""),
            "estado_civil": data.get("estado_civil", ""),
            "profesion": data.get("profesion", ""),
            "posicion": data.get("posicion", ""),
            "nacionalidad": None
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
    print(" RESULTADO PROCESADO:")
    print("="*70)
    import json
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))
    print("="*70 + "\n")
    
    return structured_data