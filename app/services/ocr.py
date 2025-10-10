# app/services/ocr.py
import re
from num2words import num2words

# Copia y pega aquí tu función parse_ocr_text completa
def parse_ocr_text(text: str):
    data = {}
    patterns = [
        ('empresa_contratante', r"EMPRESA\s+([^\n]+)"),
        ('nombre_completo', r"COLABORADOR\s+([^\n]+)"),
        ('cui', r"DPI\s*[/J]?\s*PASAPORTE\s+(\d+)"),
        ('direccion', r"DIRECCIÓN\s+([^\n]+)"),
        ('fecha_inicio', r"FECHA DE INICIO\s+([^\n]+)"),
        ('fecha_fin', r"FECHA DE FINALIZACIÓN\s+([^\n]+)"),
        ('monto', r"HONORARIOS POR PA[GC]AR\s+([\d,]+\.\d{2})"),
        ('posicion', r"POSICIÓN\s+([^\n]+)"),
        ('edad', r"EDAD\s+(\d+)")
    ]
    for key, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key == 'monto':
                value = value.replace(',', '')
            data[key] = value
    
    monto_numero = 0.0
    monto_en_letras = "CERO QUETZALES EXACTOS"
    monto_formateado = "Q.0.00"
    if data.get("monto"):
        try:
            monto_numero = float(data["monto"])
            monto_formateado = f"Q.{monto_numero:,.2f}"
            parte_entera = int(monto_numero)
            monto_en_letras = num2words(parte_entera, lang='es').upper() + " QUETZALES EXACTOS"
        except (ValueError, TypeError):
            pass
    fecha_fin_texto = data.get("fecha_fin")
    if not fecha_fin_texto or "indefinido" in fecha_fin_texto.lower():
        fecha_fin_texto = "Contrato Indefinido"

    return {
        "empresa_contratante": data.get("empresa_contratante", ""),
        "datos_persona": {
            "cui": data.get("cui", ""), "nombre_completo": data.get("nombre_completo", ""),
            "direccion": data.get("direccion", ""), "edad": data.get("edad", "")
        },
        "datos_contrato": {
            "tipo_contrato": data.get("posicion", "Servicios Profesionales"),
            "fecha_inicio": data.get("fecha_inicio", ""), "fecha_fin": fecha_fin_texto,
            "monto": monto_formateado, "monto_en_letras": monto_en_letras,
            "descripcion_adicional": f"Posición: {data.get('posicion', 'N/A')}"
        }
    }