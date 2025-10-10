from docx.document import Document
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def reemplazar_placeholders_docx(doc_obj, reemplazos: dict):
    """
    Reemplaza todos los placeholders en un documento Word (.docx).
    Maneja texto en párrafos, tablas, encabezados y pies de página.
    Preserva el formato del primer 'run' del párrafo.
    """
    
    def reemplazar_en_parrafo(parrafo: Paragraph):
        """Función interna para reemplazar texto en un párrafo."""
        texto_completo = ''.join(run.text for run in parrafo.runs)
        
        # Si no hay placeholders en todo el texto del párrafo, no hacer nada
        if not any(key in texto_completo for key in reemplazos.keys()):
            return

        # Guardar el formato del primer 'run'
        estilo_run = None
        if parrafo.runs:
            estilo_run = parrafo.runs[0]

        # Realizar todos los reemplazos en la cadena de texto completa
        for key, value in reemplazos.items():
            texto_completo = texto_completo.replace(key, str(value or ''))

        # Limpiar todos los 'runs' existentes en el párrafo
        for run in parrafo.runs:
            run.text = ''
        
        # Añadir un nuevo 'run' con el texto completo y el estilo original
        if estilo_run:
            nuevo_run = parrafo.add_run(texto_completo)
            nuevo_run.font.name = estilo_run.font.name
            nuevo_run.font.size = estilo_run.font.size
            nuevo_run.bold = estilo_run.bold
            nuevo_run.italic = estilo_run.italic
            nuevo_run.underline = estilo_run.underline
            # Puedes añadir más propiedades de estilo si las necesitas
        else:
            parrafo.add_run(texto_completo)

    def iterar_bloques(doc_part):
        """Itera sobre párrafos y tablas en una parte del documento."""
        for bloque in doc_part.iter_content():
            if isinstance(bloque, Paragraph):
                reemplazar_en_parrafo(bloque)
            elif isinstance(bloque, Table):
                for row in bloque.rows:
                    for cell in row.cells:
                        iterar_bloques(cell)

    # Procesar el cuerpo principal del documento
    iterar_bloques(doc_obj)

    # Procesar encabezados y pies de página
    for seccion in doc_obj.sections:
        iterar_bloques(seccion.header)
        iterar_bloques(seccion.footer)