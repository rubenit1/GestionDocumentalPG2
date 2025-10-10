from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()

class Placeholder(BaseModel):
    placeholder: str
    descripcion: str
    ejemplo: str

# Esta es nuestra "fuente de la verdad". Si añades un campo nuevo en el futuro,
# solo necesitas agregarlo a esta lista.
PLACEHOLDERS_LIST: List[Placeholder] = [
    # --- Datos del Colaborador ---
    Placeholder(placeholder="{{nombre_completo}}", descripcion="Nombre completo del colaborador.", ejemplo="Juan Carlos Pérez"),
    Placeholder(placeholder="{{cui}}", descripcion="CUI (DPI) del colaborador.", ejemplo="1234567890101"),
    Placeholder(placeholder="{{cui_letras}}", descripcion="CUI del colaborador en letras.", ejemplo="UNO DOS TRES..."),
    Placeholder(placeholder="{{edad_empleado}}", descripcion="Edad del colaborador en números.", ejemplo="30"),
    Placeholder(placeholder="{{edad_empleado_letras}}", descripcion="Edad del colaborador en letras.", ejemplo="TREINTA"),
    Placeholder(placeholder="{{direccion}}", descripcion="Dirección del domicilio del colaborador.", ejemplo="1ra Calle 1-23, Zona 1"),
    Placeholder(placeholder="{{estado_civil}}", descripcion="Estado civil del colaborador.", ejemplo="Soltero(a)"),
    Placeholder(placeholder="{{nacionalidad}}", descripcion="Nacionalidad del colaborador.", ejemplo="Guatemalteco(a)"),
    Placeholder(placeholder="{{profesion}}", descripcion="Profesión u oficio del colaborador.", ejemplo="Perito Contador"),
    
    # --- Datos del Contrato ---
    Placeholder(placeholder="{{fecha_contrato}}", descripcion="Fecha de celebración del contrato.", ejemplo="1 de enero de 2025"),
    Placeholder(placeholder="{{monto}}", descripcion="Monto de honorarios o salario en formato numérico.", ejemplo="Q.5,000.00"),
    Placeholder(placeholder="{{monto_letras}}", descripcion="Monto en letras.", ejemplo="CINCO MIL QUETZALES EXACTOS"),
    Placeholder(placeholder="{{puesto}}", descripcion="Posición o cargo del colaborador.", ejemplo="Asesor de Ventas"),
    
    # --- Fechas de Vigencia ---
    Placeholder(placeholder="{{día_letras}}", descripcion="Día de inicio del contrato, en letras.", ejemplo="uno"),
    Placeholder(placeholder="{{día_numeros}}", descripcion="Día de inicio del contrato, en número.", ejemplo="1"),
    Placeholder(placeholder="{{mes_letras}}", descripcion="Mes de inicio del contrato, en letras.", ejemplo="enero"),
    Placeholder(placeholder="{{año_letras}}", descripcion="Año de inicio del contrato, en letras.", ejemplo="dos mil veinticinco"),
    Placeholder(placeholder="{{año_numeros}}", descripcion="Año de inicio del contrato, en número.", ejemplo="2025"),
    # (y los equivalentes para la fecha de vencimiento: vence_dia_..., etc.)

    # --- Datos de la Empresa ---
    Placeholder(placeholder="{{empresa_entidad}}", descripcion="Razón social de la empresa contratante.", ejemplo="Innovate Solutions, S.A."),
    Placeholder(placeholder="{{empresa_lugar_notificaciones}}", descripcion="Dirección principal de la empresa.", ejemplo="Avenida Reforma 1-23, Zona 10"),
    # (y todos los demás campos de la empresa: empresa_inscrita_en, etc.)

    # --- Datos del Representante Legal ---
    Placeholder(placeholder="{{rep_legal_nombre}}", descripcion="Nombre completo del Representante Legal.", ejemplo="Ana María Rodriguez"),
    Placeholder(placeholder="{{rep_legal_edad}}", descripcion="Edad del Representante Legal.", ejemplo="45"),
    # (y todos los demás campos del representante: rep_legal_cui, etc.)
]

@router.get("/placeholders", response_model=List[Placeholder])
def get_available_placeholders():
    """
    Devuelve una lista completa de todos los placeholders (holders)
    disponibles en el sistema para usar en las plantillas.
    """
    return PLACEHOLDERS_LIST