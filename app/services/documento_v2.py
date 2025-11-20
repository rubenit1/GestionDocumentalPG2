"""
Servicio mejorado para generación de documentos usando docxtpl
Reemplaza la implementación anterior con placeholders manuales

VERSIÓN CORREGIDA:
- Formato de fecha del contrato: "el veintinueve (29) de enero del año dos mil veinticinco (2025)"
- Números en letras en minúsculas
- Números de CUI con espacios entre dígitos
"""

import datetime
import os
from docxtpl import DocxTemplate
from num2words import num2words
from sqlalchemy.orm import Session
from fastapi import HTTPException
import locale

# Configurar el locale para que los nombres de los meses salgan en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
    except locale.Error:
        print("Advertencia: No se pudo configurar el locale en español.")

from app.repository.empresa import EmpresaRepository
from app.repository.representante import RepresentanteRepository
from app.models.documento import GenerationRequest


class ServicioDocumentoV2:
    """
    Servicio mejorado para generación de documentos Word usando docxtpl
    """
    
    def __init__(self):
        self.repo_empresa = EmpresaRepository()
        self.repo_representante = RepresentanteRepository()

    def generar_documento(self, db: Session, solicitud: GenerationRequest):
        """
        Genera un documento Word a partir de una plantilla y datos del usuario
        """
        print("🚀 Iniciando generación de documento...")
        
        # 1. Obtener datos de la base de datos
        resultado_empresa = self.repo_empresa.get_by_id(db, solicitud.empresa_id)
        if not resultado_empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        resultado_representante = self.repo_representante.get_by_id(db, solicitud.representante_id)
        if not resultado_representante:
            raise HTTPException(status_code=404, detail="Representante no encontrado")
        
        print(f"✅ Empresa: {resultado_empresa['razon_social']}")
        print(f"✅ Representante: {resultado_representante['nombre_completo']}")
        
        # 2. Preparar el contexto para la plantilla
        context = self._preparar_contexto(
            resultado_empresa, 
            resultado_representante, 
            solicitud
        )
        
        print(f"✅ Contexto preparado con {len(context)} secciones")
        
        # 3. Cargar y renderizar la plantilla
        ruta_plantilla = os.path.join("templates", solicitud.template_name)
        if not os.path.exists(ruta_plantilla):
            raise HTTPException(
                status_code=404, 
                detail=f"Plantilla no encontrada: {ruta_plantilla}"
            )
        
        print(f"📄 Cargando plantilla: {ruta_plantilla}")
        
        doc = DocxTemplate(ruta_plantilla)
        doc.render(context)
        
        # 4. Guardar documento
        nombre_colaborador = context['colaborador']['nombre_completo'].replace(' ', '_')
        nombre_archivo_salida = f"contrato_generado_{nombre_colaborador}.docx"
        doc.save(nombre_archivo_salida)
        
        print(f"✅ Documento generado: {nombre_archivo_salida}")
        
        return nombre_archivo_salida

    def _preparar_contexto(self, empresa, representante, solicitud: GenerationRequest):
        """
        Prepara el contexto (diccionario) con todos los datos para la plantilla
        """
        colaborador = solicitud.colaborador_data.datos_persona
        contrato = solicitud.colaborador_data.datos_contrato
        
        rep_edad_num = (datetime.date.today() - representante['fecha_nacimiento']).days // 365
        rep_edad_letras = num2words(rep_edad_num, lang='es')
        rep_cui_letras = self._numero_a_letras_con_espacios(representante['cui'])
        rep_cui_formateado = self._formatear_cui(representante['cui'])
        
        num_registro_letras = self._convertir_numero_letras(empresa.get('numero_registro'))
        num_libro_letras = self._convertir_numero_letras(empresa.get('numero_libro'))
        num_folio_letras = self._convertir_numero_letras(empresa.get('numero_folio'))
        
        colab_cui_letras = self._numero_a_letras_con_espacios(colaborador.cui) if colaborador.cui else ""
        colab_cui_formateado = self._formatear_cui(colaborador.cui) if colaborador.cui else ""
        colab_edad_letras = num2words(int(colaborador.edad), lang='es') if colaborador.edad and colaborador.edad.isdigit() else ""
        
        fecha_inicio_data = self._procesar_fecha(contrato.fecha_inicio)
        fecha_fin_data = self._procesar_fecha(contrato.fecha_fin)
        
        fecha_contrato_formateada = self._formato_fecha_contrato(solicitud.fecha_contrato)
        
        colab_nombre_titulo = self._titulo_mayusculas(colaborador.nombre_completo)

        context = {
            'colaborador': {
                'nombre_completo': colaborador.nombre_completo or '',
                'nombre_completo_titulo': colab_nombre_titulo,
                'cui': colaborador.cui or '',
                'cui_formateado': colab_cui_formateado,
                'cui_letras': colab_cui_letras,
                'edad': colaborador.edad or '',
                'edad_letras': colab_edad_letras,
                'direccion': colaborador.direccion or '',
                'estado_civil': colaborador.estado_civil or 'Soltero',
                'nacionalidad': colaborador.nacionalidad or 'Guatemalteco',
                'profesion': colaborador.profesion or 'N/A',
                'posicion': colaborador.posicion or contrato.tipo_contrato or '',
                'lugar_notificaciones': colaborador.direccion or '',
                'puesto': colaborador.posicion or contrato.tipo_contrato or '',
            },
            
            'empresa': {
                'razon_social': empresa['razon_social'],
                'autorizada_en': empresa.get('autorizada_en', ''),
                'fecha_autorizacion': self._formato_fecha_largo(empresa.get('fecha_autorizacion')),
                'autorizada_por': empresa.get('autorizada_por', ''),
                'inscrita_en': empresa.get('inscrita_en', ''),
                'numero_registro': empresa.get('numero_registro', ''),
                'numero_registro_letras': num_registro_letras,
                'numero_folio': empresa.get('numero_folio', ''),
                'numero_folio_letras': num_folio_letras,
                'numero_libro': empresa.get('numero_libro', ''),
                'numero_libro_letras': num_libro_letras,
                'tipo_libro': empresa.get('tipo_libro', ''),
                'lugar_notificaciones': empresa.get('lugar_notificaciones', ''),
                'segundo_lugar_notificaciones': empresa.get('segundo_lugar_notificaciones', ''),
            },
            
            'representante': {
                'nombre_completo': representante['nombre_completo'],
                'edad': str(rep_edad_num),
                'edad_letras': rep_edad_letras,
                'estado_civil': representante.get('estado_civil', ''),
                'profesion': representante.get('profesion', ''),
                'nacionalidad': representante.get('nacionalidad', ''),
                'cui': representante['cui'],
                'cui_formateado': rep_cui_formateado,
                'cui_letras': rep_cui_letras,
                'extendido_en': representante.get('extendido_en', ''),
            },
            
            'contrato': {
                'fecha': fecha_contrato_formateada,
                'monto': contrato.monto or 'Q.0.00',
                'monto_letras': contrato.monto_en_letras or 'CERO QUETZALES EXACTOS',
                'tipo': contrato.tipo_contrato or 'Servicios Profesionales',
            },
            
            'fecha_inicio': fecha_inicio_data,
            'fecha_fin': fecha_fin_data,
            'genero': 'El Notario',
            'puesto': colaborador.posicion or contrato.tipo_contrato or '',
        }
        
        return context

    def _titulo_mayusculas(self, texto):
        if not texto:
            return ''
        return texto.title()

    def _formato_fecha_contrato(self, fecha_str):
        meses_esp = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        try:
            fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            dia_num = fecha.day
            dia_letras = num2words(dia_num, lang='es')
            mes_nombre = meses_esp[fecha.month]
            anio_num = fecha.year
            anio_letras = num2words(anio_num, lang='es')
            return f"el {dia_letras} ({dia_num}) de {mes_nombre} del año {anio_letras} ({anio_num})"
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error al formatear fecha del contrato: {e}")
            return fecha_str

    def _procesar_fecha(self, fecha_str):
        """
        Procesa fecha en formato dd/mm/yyyy o yyyy-mm-dd
        """
        meses_esp = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        if not fecha_str or "indefinido" in str(fecha_str).lower():
            return {
                'dia': 'N/A', 
                'dia_letras': 'N/A', 
                'mes': 'N/A', 
                'anio': 'N/A', 
                'anio_letras': 'N/A', 
                'completa': 'Por tiempo indefinido'
            }
        
        try:
            # Intentar formato dd/mm/yyyy primero (del OCR)
            if '/' in fecha_str:
                fecha = datetime.datetime.strptime(fecha_str, "%d/%m/%Y")
            else:
                # Formato yyyy-mm-dd
                fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            
            mes_nombre = meses_esp[fecha.month]
            return {
                'dia': fecha.day, 
                'dia_letras': num2words(fecha.day, lang='es'), 
                'mes': mes_nombre, 
                'anio': fecha.year, 
                'anio_letras': num2words(fecha.year, lang='es'), 
                'completa': f"{fecha.day} de {mes_nombre} de {fecha.year}"
            }
        except (ValueError, TypeError, AttributeError):
            return {
                'dia': 'N/A', 
                'dia_letras': 'N/A', 
                'mes': 'N/A', 
                'anio': 'N/A', 
                'anio_letras': 'N/A', 
                'completa': 'Fecha no especificada'
            }

    def _formato_fecha_largo(self, objeto_fecha):
        meses_esp = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        if not isinstance(objeto_fecha, (datetime.date, datetime.datetime)):
            return ""
        day_num = objeto_fecha.day
        day_letras = num2words(day_num, lang='es')
        month_name = meses_esp[objeto_fecha.month]
        return f"el {day_letras} ({day_num}) de {month_name} de {objeto_fecha.year}"

    def _numero_a_letras_con_espacios(self, numero_str):
        if not numero_str or not str(numero_str).isdigit():
            return ''
        numero_str = numero_str.replace(' ', '').replace('-', '')
        if len(numero_str) != 13:
            return ' '.join(num2words(int(d), lang='es') for d in str(numero_str))
        grupo1 = numero_str[0:4]
        grupo2 = numero_str[4:9]
        grupo3 = numero_str[9:13]
        grupo1_letras = num2words(int(grupo1), lang='es')
        grupo2_letras = num2words(int(grupo2), lang='es')
        grupo3_letras = num2words(int(grupo3), lang='es')
        return f"{grupo1_letras} espacio {grupo2_letras} espacio {grupo3_letras}"

    def _formatear_cui(self, numero_str):
        if not numero_str or not str(numero_str).isdigit():
            return numero_str or ''
        numero_str = numero_str.replace(' ', '').replace('-', '')
        if len(numero_str) != 13:
            return numero_str
        grupo1 = numero_str[0:4]
        grupo2 = numero_str[4:9]
        grupo3 = numero_str[9:13]
        return f"{grupo1} {grupo2} {grupo3}"

    def _convertir_numero_letras(self, numero_str):
        if not numero_str:
            return ''
        try:
            if str(numero_str).isdigit():
                return num2words(int(numero_str), lang='es')
            else:
                return str(numero_str)
        except (ValueError, TypeError):
            return str(numero_str)