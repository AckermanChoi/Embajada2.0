from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from datetime import date
import mysql.connector
import re

# Importamos las funciones que consultan/insertan/eliminan en MySQL
from app.database import (
    fetch_all_residentes, 
    insert_residente, 
    delete_residente,
    fetch_residente_by_id,
    update_residente
)


@dataclass
class ResidenteRecord:
    id: int
    nombre: str
    apellido: str
    fecha_nacimiento: date
    pasaporte: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ocupacion: Optional[str] = None
    estado_civil: Optional[str] = None


app = FastAPI(title="Sistema de Gestión de Residentes - Embajada")

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Motor de plantillas
templates = Jinja2Templates(directory="app/templates")


# --- Manejador de errores 404 ---
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Manejador personalizado para errores HTTP.
    Muestra una página de error personalizada para errores 404.
    """
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "pages/error_404.html",
            {
                "request": request
            },
            status_code=404
        )
    return templates.TemplateResponse(
        "pages/error_500.html",
        {
            "request": request
        },
        status_code=500
    )


# --- Manejador de errores de base de datos ---
@app.exception_handler(mysql.connector.Error)
async def database_exception_handler(request: Request, exc: mysql.connector.Error):
    """
    Manejador personalizado para errores de MySQL.
    Muestra una página de error 500 cuando hay problemas de conexión.
    """
    return templates.TemplateResponse(
        "pages/error_500.html",
        {
            "request": request
        },
        status_code=500
    )


# --- Manejador de errores generales del servidor ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Manejador personalizado para excepciones no controladas.
    Muestra una página de error 500 genérica.
    """
    # Log del error para debugging (opcional)
    print(f"Error no controlado: {type(exc).__name__}: {str(exc)}")
    
    return templates.TemplateResponse(
        "pages/error_500.html",
        {
            "request": request
        },
        status_code=500
    )


def map_rows_to_residentes(rows: List[dict]) -> List[ResidenteRecord]:
    """
    Convierte las filas del SELECT * FROM residentes (dict) 
    en objetos ResidenteRecord (sin validaciones estrictas para datos existentes).
    """
    return [
        ResidenteRecord(
            id=row["id"],
            nombre=row["nombre"],
            apellido=row["apellido"],
            fecha_nacimiento=row["fecha_nacimiento"],
            pasaporte=row["pasaporte"],
            email=row["email"],
            telefono=row.get("telefono"),
            direccion=row.get("direccion"),
            ocupacion=row.get("ocupacion"),
            estado_civil=row.get("estado_civil"),
        )
        for row in rows
    ]


def validar_nombre_apellido(value: str) -> str:
    if not value or not value.strip():
        raise ValueError('El campo no puede estar vacío')

    value = value.strip()

    if len(value) < 2:
        raise ValueError('Debe tener al menos 2 caracteres')

    if len(value) > 100:
        raise ValueError('No puede exceder 100 caracteres')

    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', value):
        raise ValueError('Solo se permiten letras y espacios')

    return value.title()


def validar_fecha_nacimiento(value: date) -> date:
    if value > date.today():
        raise ValueError('La fecha de nacimiento no puede ser futura')

    edad_aprox = (date.today() - value).days // 365
    if edad_aprox > 150:
        raise ValueError('La fecha de nacimiento no es válida')

    return value


def validar_pasaporte(value: str) -> str:
    if not value or not value.strip():
        raise ValueError('El pasaporte es obligatorio')

    value = value.strip().upper()

    if len(value) < 6:
        raise ValueError('El pasaporte debe tener al menos 6 caracteres')

    if len(value) > 50:
        raise ValueError('El pasaporte no puede exceder 50 caracteres')

    if not re.match(r'^[A-Z0-9\-]+$', value):
        raise ValueError('El pasaporte solo puede contener letras, números y guiones')

    return value


def validar_email(value: str) -> str:
    if not value or not value.strip():
        raise ValueError('El correo electrónico es obligatorio')

    value = value.strip()

    if len(value) > 150:
        raise ValueError('El correo electrónico no puede exceder 150 caracteres')

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value):
        raise ValueError('El correo electrónico no tiene un formato válido')

    return value


def validar_telefono(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip() == '':
        return None

    value = value.strip()
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', value)

    if not re.match(r'^\+?\d{7,15}$', telefono_limpio):
        raise ValueError('Formato de teléfono inválido. Debe contener entre 7 y 15 dígitos')

    return value


def validar_direccion(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip() == '':
        return None

    value = value.strip()

    if len(value) > 255:
        raise ValueError('La dirección no puede exceder 255 caracteres')

    return value


def validar_ocupacion(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip() == '':
        return None

    value = value.strip()

    if len(value) > 100:
        raise ValueError('La ocupación no puede exceder 100 caracteres')

    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-]+$', value):
        raise ValueError('La ocupación solo puede contener letras, espacios, puntos y guiones')

    return value.title()


def validar_estado_civil(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip() == '':
        return None

    value = value.strip().title()

    estados_validos = [
        'Soltero',
        'Soltera',
        'Casado',
        'Casada',
        'Divorciado',
        'Divorciada',
        'Viudo',
        'Viuda',
        'Unión Libre'
    ]

    if value not in estados_validos:
        raise ValueError(f'Estado civil inválido. Opciones válidas: {", ".join(estados_validos)}')

    return value


def validar_residente_form(
    nombre: str,
    apellido: str,
    fecha_nacimiento: date,
    pasaporte: str,
    email: str,
    telefono: Optional[str],
    direccion: Optional[str],
    ocupacion: Optional[str],
    estado_civil: Optional[str]
) -> Tuple[Optional[Dict[str, object]], List[str]]:
    errores: List[str] = []
    data: Dict[str, object] = {}

    try:
        data["nombre"] = validar_nombre_apellido(nombre)
    except ValueError as exc:
        errores.append(f"Nombre: {exc}")

    try:
        data["apellido"] = validar_nombre_apellido(apellido)
    except ValueError as exc:
        errores.append(f"Apellido: {exc}")

    try:
        data["fecha_nacimiento"] = validar_fecha_nacimiento(fecha_nacimiento)
    except ValueError as exc:
        errores.append(f"Fecha de nacimiento: {exc}")

    try:
        data["pasaporte"] = validar_pasaporte(pasaporte)
    except ValueError as exc:
        errores.append(f"Pasaporte: {exc}")

    try:
        data["email"] = validar_email(email)
    except ValueError as exc:
        errores.append(f"Email: {exc}")

    try:
        data["telefono"] = validar_telefono(telefono)
    except ValueError as exc:
        errores.append(f"Telefono: {exc}")

    try:
        data["direccion"] = validar_direccion(direccion)
    except ValueError as exc:
        errores.append(f"Direccion: {exc}")

    try:
        data["ocupacion"] = validar_ocupacion(ocupacion)
    except ValueError as exc:
        errores.append(f"Ocupacion: {exc}")

    try:
        data["estado_civil"] = validar_estado_civil(estado_civil)
    except ValueError as exc:
        errores.append(f"Estado civil: {exc}")

    if errores:
        return None, errores

    return data, []


# --- GET principal ---
@app.get("/", response_class=HTMLResponse)
def get_index(request: Request):
    # 1️⃣ Obtenemos los datos desde MySQL
    rows = fetch_all_residentes()

    # 2️⃣ Convertimos cada fila a Residente (valida estructura)
    residentes = map_rows_to_residentes(rows)

    # 3️⃣ Enviamos a la plantilla
    return templates.TemplateResponse(
        "pages/index.html",
        {
            "request": request,
            "residentes": residentes
        }
    )


# --- GET formulario nuevo residente ---
@app.get("/residentes/nuevo", response_class=HTMLResponse)
def get_nuevo_residente(request: Request):
    return templates.TemplateResponse(
        "pages/nuevo_residente.html",
        {
            "request": request,
            "mensaje": None
        }
    )


# --- POST guardar nuevo residente ---
@app.post("/residentes/nuevo")
def post_nuevo_residente(
    request: Request,
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: date = Form(...),
    pasaporte: str = Form(...),
    email: str = Form(...),
    telefono: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    ocupacion: Optional[str] = Form(None),
    estado_civil: Optional[str] = Form(None)
):
    validado, errores = validar_residente_form(
        nombre,
        apellido,
        fecha_nacimiento,
        pasaporte,
        email,
        telefono,
        direccion,
        ocupacion,
        estado_civil
    )

    if errores:
        return templates.TemplateResponse(
            "pages/nuevo_residente.html",
            {
                "request": request,
                "mensaje": None,
                "errores": errores,
                "nombre": nombre,
                "apellido": apellido,
                "fecha_nacimiento": fecha_nacimiento,
                "pasaporte": pasaporte,
                "email": email,
                "telefono": telefono,
                "direccion": direccion,
                "ocupacion": ocupacion,
                "estado_civil": estado_civil
            },
            status_code=422
        )

    insert_residente(
        validado["nombre"],
        validado["apellido"],
        str(validado["fecha_nacimiento"]),
        validado["pasaporte"],
        validado["email"],
        validado["telefono"],
        validado["direccion"],
        validado["ocupacion"],
        validado["estado_civil"]
    )

    return RedirectResponse(url="/", status_code=303)


# --- POST eliminar residente ---
@app.post("/residentes/eliminar/{residente_id}")
def post_eliminar_residente(request: Request, residente_id: int):
    """
    Endpoint para eliminar un residente por su ID.
    """
    eliminado = delete_residente(residente_id)

    if not eliminado:
        return templates.TemplateResponse(
            "pages/error_404.html",
            {
                "request": request
            },
            status_code=404
        )

    return RedirectResponse(url="/", status_code=303)


# --- GET formulario editar residente ---
@app.get("/residentes/editar/{residente_id}", response_class=HTMLResponse)
def get_editar_residente(request: Request, residente_id: int):
    """
    Endpoint para mostrar el formulario de edición con datos precargados.
    """
    # Obtenemos los datos del residente
    residente_data = fetch_residente_by_id(residente_id)
    
    if not residente_data:
        return templates.TemplateResponse(
            "pages/error_404.html",
            {
                "request": request
            },
            status_code=404
        )
    
    # Convertimos a modelo ResidenteRecord para mostrar en formulario (sin validaciones)
    residente = ResidenteRecord(**residente_data)
    
    return templates.TemplateResponse(
        "pages/editar_residente.html",
        {
            "request": request,
            "residente": residente
        }
    )


# --- POST actualizar residente ---
@app.post("/residentes/editar/{residente_id}")
def post_editar_residente(
    request: Request,
    residente_id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: date = Form(...),
    pasaporte: str = Form(...),
    email: str = Form(...),
    telefono: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    ocupacion: Optional[str] = Form(None),
    estado_civil: Optional[str] = Form(None)
):
    """
    Endpoint para actualizar los datos de un residente.
    """
    validado, errores = validar_residente_form(
        nombre,
        apellido,
        fecha_nacimiento,
        pasaporte,
        email,
        telefono,
        direccion,
        ocupacion,
        estado_civil
    )

    if errores:
        residente_temp = ResidenteRecord(
            id=residente_id,
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            email=email,
            telefono=telefono,
            direccion=direccion,
            ocupacion=ocupacion,
            estado_civil=estado_civil
        )

        return templates.TemplateResponse(
            "pages/editar_residente.html",
            {
                "request": request,
                "residente": residente_temp,
                "errores": errores
            },
            status_code=422
        )

    actualizado = update_residente(
        residente_id,
        validado["nombre"],
        validado["apellido"],
        str(validado["fecha_nacimiento"]),
        validado["pasaporte"],
        validado["email"],
        validado["telefono"],
        validado["direccion"],
        validado["ocupacion"],
        validado["estado_civil"]
    )

    if not actualizado:
        return templates.TemplateResponse(
            "pages/error_404.html",
            {
                "request": request
            },
            status_code=404
        )

    return RedirectResponse(url="/", status_code=303)
