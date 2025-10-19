# app/services/documento_v2.py
"""
Servicio mejorado para generación de documentos usando docxtpl
Reemplaza la implementación anterior con placeholders manuales
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
        
        Args:
            db: Sesión de base de datos
            solicitud: Datos de la solicitud (empresa_id, representante_id, datos OCR)
            
        Returns:
            str: Nombre del archivo generado
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
        
        # Cargar plantilla con docxtpl
        doc = DocxTemplate(ruta_plantilla)
        
        # Renderizar con el contexto
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
        
        Returns:
            dict: Contexto estructurado para docxtpl
        """
        colaborador = solicitud.colaborador_data.datos_persona
        contrato = solicitud.colaborador_data.datos_contrato
        
        # --- CALCULAR EDAD DEL REPRESENTANTE ---
        rep_edad_num = (datetime.date.today() - representante['fecha_nacimiento']).days // 365
        rep_edad_letras = num2words(rep_edad_num, lang='es').upper()
        rep_cui_letras = self._numero_a_letras(representante['cui'])
        
        # --- PROCESAR NÚMEROS DE EMPRESA ---
        num_registro_letras = self._convertir_numero_letras(empresa.get('numero_registro'))
        num_libro_letras = self._convertir_numero_letras(empresa.get('numero_libro'))
        num_folio_letras = self._convertir_numero_letras(empresa.get('numero_folio'))
        
        # --- DATOS DEL COLABORADOR ---
        colab_cui_letras = self._numero_a_letras(colaborador.cui) if colaborador.cui else ""
        colab_edad_letras = num2words(int(colaborador.edad), lang='es').upper() if colaborador.edad and colaborador.edad.isdigit() else ""
        
        # --- PROCESAR FECHAS ---
        fecha_inicio_data = self._procesar_fecha(contrato.fecha_inicio)
        fecha_fin_data = self._procesar_fecha(contrato.fecha_fin)
        
        # --- CONSTRUIR CONTEXTO ---
        context = {
            # COLABORADOR
            'colaborador': {
                'nombre_completo': colaborador.nombre_completo or '',
                'cui': colaborador.cui or '',
                'cui_letras': colab_cui_letras,
                'edad': colaborador.edad or '',
                'edad_letras': colab_edad_letras,
                'direccion': colaborador.direccion or '',
                'estado_civil': colaborador.estado_civil or 'Soltero',
                'nacionalidad': colaborador.nacionalidad or 'Guatemalteco',
                'profesion': colaborador.profesion or 'N/A',
                'posicion': colaborador.posicion or contrato.tipo_contrato or '',
                'lugar_notificaciones': colaborador.direccion or '',
            },
            
            # EMPRESA
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
            
            # REPRESENTANTE LEGAL
            'representante': {
                'nombre_completo': representante['nombre_completo'],
                'edad': str(rep_edad_num),
                'edad_letras': rep_edad_letras,
                'estado_civil': representante.get('estado_civil', ''),
                'profesion': representante.get('profesion', ''),
                'nacionalidad': representante.get('nacionalidad', ''),
                'cui': representante['cui'],
                'cui_letras': rep_cui_letras,
                'extendido_en': representante.get('extendido_en', ''),
            },
            
            # DATOS DEL CONTRATO
            'contrato': {
                'fecha': solicitud.fecha_contrato,
                'monto': contrato.monto or 'Q.0.00',
                'monto_letras': contrato.monto_en_letras or 'CERO QUETZALES EXACTOS',
                'tipo': contrato.tipo_contrato or 'Servicios Profesionales',
            },
            
            # FECHA DE INICIO
            'fecha_inicio': fecha_inicio_data,
            
            # FECHA DE FIN
            'fecha_fin': fecha_fin_data,
            
            # GÉNERO (para notarios)
            'genero': 'El Notario',  # Valor por defecto
            
            # ALIAS PARA COMPATIBILIDAD
            'puesto': colaborador.posicion or contrato.tipo_contrato or '',
        }
        
        return context

    def _procesar_fecha(self, fecha_str):
        """
        Procesa una fecha string y retorna un diccionario con diferentes formatos
        """
        if not fecha_str or "indefinido" in fecha_str.lower():
            return {
                'dia': 'N/A',
                'dia_letras': 'N/A',
                'mes': 'N/A',
                'anio': 'N/A',
                'anio_letras': 'N/A',
                'completa': 'Por tiempo indefinido'
            }
        
        try:
            fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            return {
                'dia': fecha.day,
                'dia_letras': num2words(fecha.day, lang='es'),
                'mes': fecha.strftime('%B'),
                'anio': fecha.year,
                'anio_letras': num2words(fecha.year, lang='es'),
                'completa': fecha.strftime('%d de %B de %Y')
            }
        except (ValueError, TypeError):
            return {
                'dia': 'N/A',
                'dia_letras': 'N/A',
                'mes': 'N/A',
                'anio': 'N/A',
                'anio_letras': 'N/A',
                'completa': 'Fecha no especificada'
            }

    def _formato_fecha_largo(self, objeto_fecha):
        """
        Formatea una fecha en formato largo: "el cinco (5) de enero de 2025"
        """
        if not isinstance(objeto_fecha, (datetime.date, datetime.datetime)):
            return ""
        
        day_num = objeto_fecha.day
        day_letras = num2words(day_num, lang='es')
        month_name = objeto_fecha.strftime('%B')
        
        return f"el {day_letras} ({day_num}) de {month_name} de {objeto_fecha.year}"

    def _numero_a_letras(self, numero_str):
        """
        Convierte cada dígito de un número a letras
        Ejemplo: "123" -> "UNO DOS TRES"
        """
        if not numero_str or not str(numero_str).isdigit():
            return ''
        
        return ' '.join(num2words(int(d), lang='es') for d in str(numero_str)).upper()

    def _convertir_numero_letras(self, numero_str):
        """
        Convierte un número completo a letras
        Ejemplo: "123" -> "CIENTO VEINTITRÉS"
        """
        if not numero_str:
            return ''
        
        try:
            if str(numero_str).isdigit():
                return num2words(int(numero_str), lang='es').upper()
            else:
                return str(numero_str)
        except (ValueError, TypeError):
            return str(numero_str)
