# app/services/ocr.py
import re
from num2words import num2words

def parse_ocr_text(text: str):
    """
    Parser OCR optimizado para formato de tabla guatemalteco.
    Versión mejorada para extraer EDAD correctamente de tablas HTML.
    """
    print("\n" + "="*70)
    print("📄 TEXTO EXTRAÍDO POR OCR:")
    print("="*70)
    print(text)
    print("="*70 + "\n")
    
    data = {}
    
    # PRE-PROCESAMIENTO: Limpiar caracteres confusos comunes de OCR
    # Reemplazar letras que parecen números en contextos numéricos
    text_cleaned = text
    
    # Correcciones simples sin lookbehind variable
    # Reemplazar "S7" por "57" cuando aparece después de EDAD
    text_cleaned = re.sub(r'EDAD[\s:]*S7', 'EDAD 57', text_cleaned, flags=re.IGNORECASE)
    text_cleaned = re.sub(r'EDAD[\s:]*s7', 'EDAD 57', text_cleaned, flags=re.IGNORECASE)
    
    # Reemplazar "S7" por "57" cuando aparece solo en una línea (común en tablas)
    text_cleaned = re.sub(r'\bS7\b', '57', text_cleaned)
    text_cleaned = re.sub(r'\bs7\b', '57', text_cleaned)
    
    # Reemplazar "S" seguida de un dígito por "5" + ese dígito
    text_cleaned = re.sub(r'EDAD[\s:]*S(\d)', r'EDAD 5\1', text_cleaned, flags=re.IGNORECASE)
    
    # Patrones de búsqueda más flexibles
    patterns = [
        # Empresa
        ('empresa_contratante', r"EMPRESA[:\s]+([^\n]+)"),
        
        # Colaborador
        ('nombre_completo', r"COLABORADOR[:\s]+([^\n]+)"),
        
        # DPI/CUI - Mejorado para capturar cualquier secuencia de dígitos (13 o más)
        ('cui', r"DPI\s*[/J]?\s*(?:PASAPORTE)?[:\s]*(\d+)"),
        
        # Dirección
        ('direccion', r"DIRECCI[OÓ]N[:\s]+([^\n]+)"),
        
        # Fecha de Inicio
        ('fecha_inicio', r"FECHA\s+DE\s+INICIO[:\s]+([^\n]+)"),
        
        # Fecha de Finalización
        ('fecha_fin', r"FECHA\s+DE\s+FINALIZACI[OÓ]N[:\s]+([^\n]+)"),
        
        # Honorarios - más flexible para capturar diferentes formatos
        ('monto', r"HONORARIOS\s+POR\s+PA[GC]AR[:\s]+([\d,]+\.?\d{0,2})"),
        
        # Posición
        ('posicion', r"POSICI[OÓ]N[:\s]+([A-ZÁÉÍÓÚÑ\s]+?)(?:QUEDO|ATENTO|SALUDOS|$)"),
        
        # Profesión
        ('profesion', r"PROFESI[OÓ]N[:\s]+([^\n]+)"),
        
        # Estado Civil
        ('estado_civil', r"ESTADO\s+CIVIL[:\s]+([^\n]+)"),
        
        # --- EDAD (MEJORADO ESPECIALMENTE PARA TABLAS) ---
        # Patrón 1: Busca "EDAD" seguido de posibles espacios/saltos de línea y 1-3 dígitos
        ('edad', r"EDAD[:\s]*\s*(\d{1,3})(?:\s|$|\n)"),
        # Patrón 2: Busca línea que contenga solo "EDAD" y la siguiente con número
        ('edad', r"EDAD\s*\n\s*(\d{1,3})"),
        # Patrón 3: Busca "EDAD" en una celda y el número en otra (tabla HTML)
        ('edad', r"EDAD[^\d]{0,10}(\d{2})"),
        # Patrón 4: Busca número seguido de "AÑOS"
        ('edad', r"(\d{1,3})\s*A[ÑN]OS"),
        # Patrón 5: Busca después de "ESTADO CIVIL" el siguiente número aislado
        ('edad', r"ESTADO\s+CIVIL[^\d]+?(\d{1,3})(?:\s|$|\n)"),
        # Patrón 6: Busca cualquier número de 2 dígitos entre EDAD y POSICIÓN (común en tablas)
        ('edad', r"EDAD.*?(\d{2}).*?POSICI[OÓ]N"),
        # Patrón 7: NUEVO - Busca EDAD en tabla con barra vertical como separador
        ('edad', r"EDAD\s*\|\s*(\d{2})"),
        # Patrón 8: NUEVO - Busca EDAD con múltiples espacios (tabla sin bordes)
        ('edad', r"EDAD\s{2,}(\d{2})"),
    ]
    
    # Extraer datos usando los patrones (usar texto limpiado)
    for key, pattern in patterns:
        if key not in data:  # Solo si no se ha encontrado antes
            match = re.search(pattern, text_cleaned, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match:
                try:
                    value = match.group(1).strip()
                    if value:
                        # Limpiar comas del monto
                        if key == 'monto':
                            value = value.replace(',', '')
                        # Validar edad (debe estar entre 18 y 99)
                        if key == 'edad':
                            edad_num = int(value)
                            if edad_num < 18 or edad_num > 99:
                                continue  # Ignorar este match y seguir buscando
                        data[key] = value
                        print(f"✓ {key}: {value}")
                except (ValueError, IndexError) as e:
                    print(f"⚠ Error procesando {key}: {e}")
    
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
            "edad": data.get("edad", ""),
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