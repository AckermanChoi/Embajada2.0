from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, EmailStr, field_validator, ValidationError
from typing import Optional, List
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


# Modelo base con validaciones comunes
class ResidenteBase(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    pasaporte: str
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ocupacion: Optional[str] = None
    estado_civil: Optional[str] = None
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre_apellido(cls, v: str) -> str:
        """Valida que nombre y apellido tengan formato correcto."""
        if not v or not v.strip():
            raise ValueError('El campo no puede estar vacío')
        
        v = v.strip()
        
        if len(v) < 2:
            raise ValueError('Debe tener al menos 2 caracteres')
        
        if len(v) > 100:
            raise ValueError('No puede exceder 100 caracteres')
        
        # Solo letras, espacios, tildes y caracteres especiales del español
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', v):
            raise ValueError('Solo se permiten letras y espacios')
        
        return v.title()  # Capitaliza cada palabra
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validar_fecha_nacimiento(cls, v: date) -> date:
        """Valida que la fecha de nacimiento sea válida."""
        from datetime import date as date_class
        
        # Verificar que no sea una fecha futura
        if v > date_class.today():
            raise ValueError('La fecha de nacimiento no puede ser futura')
        
        # Verificar que la persona no sea mayor de 150 años
        edad_aprox = (date_class.today() - v).days // 365
        if edad_aprox > 150:
            raise ValueError('La fecha de nacimiento no es válida')
        
        return v
    
    @field_validator('pasaporte')
    @classmethod
    def validar_pasaporte(cls, v: str) -> str:
        """Valida el formato del pasaporte."""
        if not v or not v.strip():
            raise ValueError('El pasaporte es obligatorio')
        
        v = v.strip().upper()
        
        if len(v) < 6:
            raise ValueError('El pasaporte debe tener al menos 6 caracteres')
        
        if len(v) > 50:
            raise ValueError('El pasaporte no puede exceder 50 caracteres')
        
        # Formato alfanumérico básico (letras y números, opcionalmente guiones)
        if not re.match(r'^[A-Z0-9\-]+$', v):
            raise ValueError('El pasaporte solo puede contener letras, números y guiones')
        
        return v
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida el formato del teléfono."""
        if v is None or v.strip() == '':
            return None
        
        v = v.strip()
        
        # Elimina espacios, guiones y paréntesis para validar
        telefono_limpio = re.sub(r'[\s\-\(\)]', '', v)
        
        # Debe contener solo dígitos y opcionalmente + al inicio
        if not re.match(r'^\+?\d{7,15}$', telefono_limpio):
            raise ValueError('Formato de teléfono inválido. Debe contener entre 7 y 15 dígitos')
        
        return v
    
    @field_validator('direccion')
    @classmethod
    def validar_direccion(cls, v: Optional[str]) -> Optional[str]:
        """Valida la dirección."""
        if v is None or v.strip() == '':
            return None
        
        v = v.strip()
        
        if len(v) > 255:
            raise ValueError('La dirección no puede exceder 255 caracteres')
        
        return v
    
    @field_validator('ocupacion')
    @classmethod
    def validar_ocupacion(cls, v: Optional[str]) -> Optional[str]:
        """Valida la ocupación."""
        if v is None or v.strip() == '':
            return None
        
        v = v.strip()
        
        if len(v) > 100:
            raise ValueError('La ocupación no puede exceder 100 caracteres')
        
        # Solo letras, espacios y algunos caracteres especiales
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-]+$', v):
            raise ValueError('La ocupación solo puede contener letras, espacios, puntos y guiones')
        
        return v.title()
    
    @field_validator('estado_civil')
    @classmethod
    def validar_estado_civil(cls, v: Optional[str]) -> Optional[str]:
        """Valida el estado civil."""
        if v is None or v.strip() == '':
            return None
        
        v = v.strip().title()
        
        # Lista de estados civiles válidos
        estados_validos = ['Soltero', 'Soltera', 'Casado', 'Casada', 'Divorciado', 'Divorciada', 
                          'Viudo', 'Viuda', 'Unión Libre']
        
        if v not in estados_validos:
            raise ValueError(f'Estado civil inválido. Opciones válidas: {", ".join(estados_validos)}')
        
        return v


# Modelo para lectura de BD (sin validaciones estrictas, acepta datos históricos)
class ResidenteDB(BaseModel):
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


# Modelo para crear residente (sin ID)
class ResidenteCreate(ResidenteBase):
    pass


# Modelo para actualizar residente (sin ID)
class ResidenteUpdate(ResidenteBase):
    pass


# Modelo completo de Residente (con ID y validaciones)
class Residente(ResidenteBase):
    id: int


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
    # Para otros errores HTTP, retornar respuesta JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
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


def map_rows_to_residentes(rows: List[dict]) -> List[ResidenteDB]:
    """
    Convierte las filas del SELECT * FROM residentes (dict) 
    en objetos ResidenteDB (sin validaciones estrictas para datos existentes).
    """
    return [
        ResidenteDB(
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
    try:
        # Validamos los datos usando Pydantic
        residente_data = ResidenteCreate(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            email=email,
            telefono=telefono if telefono else None,
            direccion=direccion if direccion else None,
            ocupacion=ocupacion if ocupacion else None,
            estado_civil=estado_civil if estado_civil else None
        )
        
        # Insertamos el residente en la base de datos
        insert_residente(
            residente_data.nombre,
            residente_data.apellido,
            str(residente_data.fecha_nacimiento),
            residente_data.pasaporte,
            residente_data.email,
            residente_data.telefono,
            residente_data.direccion,
            residente_data.ocupacion,
            residente_data.estado_civil
        )
        
        # Redirigimos al inicio para ver el listado actualizado
        return RedirectResponse(url="/", status_code=303)
        
    except ValidationError as e:
        # Extraemos los errores de validación
        errores = []
        for error in e.errors():
            campo = str(error['loc'][0]) if error['loc'] else 'campo'
            mensaje = error['msg']
            errores.append(f"{campo.capitalize()}: {mensaje}")
        
        # Mostramos el formulario con los errores
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


# --- DELETE eliminar residente ---
@app.delete("/residentes/{residente_id}")
def delete_residente_endpoint(residente_id: int):
    """
    Endpoint para eliminar un residente por su ID.
    """
    eliminado = delete_residente(residente_id)
    
    if not eliminado:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    
    return JSONResponse(
        content={"mensaje": "Residente eliminado exitosamente"},
        status_code=200
    )


# --- GET formulario editar residente ---
@app.get("/residentes/editar/{residente_id}", response_class=HTMLResponse)
def get_editar_residente(request: Request, residente_id: int):
    """
    Endpoint para mostrar el formulario de edición con datos precargados.
    """
    # Obtenemos los datos del residente
    residente_data = fetch_residente_by_id(residente_id)
    
    if not residente_data:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    
    # Convertimos a modelo ResidenteDB para mostrar en formulario (sin validaciones)
    residente = ResidenteDB(**residente_data)
    
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
    try:
        # Validamos los datos usando Pydantic
        residente_data = ResidenteUpdate(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            email=email,
            telefono=telefono if telefono else None,
            direccion=direccion if direccion else None,
            ocupacion=ocupacion if ocupacion else None,
            estado_civil=estado_civil if estado_civil else None
        )
        
        # Actualizamos el residente en la base de datos
        actualizado = update_residente(
            residente_id,
            residente_data.nombre,
            residente_data.apellido,
            str(residente_data.fecha_nacimiento),
            residente_data.pasaporte,
            residente_data.email,
            residente_data.telefono,
            residente_data.direccion,
            residente_data.ocupacion,
            residente_data.estado_civil
        )
        
        if not actualizado:
            raise HTTPException(status_code=404, detail="Residente no encontrado")
        
        # Redirigimos al inicio para ver el listado actualizado
        return RedirectResponse(url="/", status_code=303)
        
    except ValidationError as e:
        # Extraemos los errores de validación
        errores = []
        for error in e.errors():
            campo = str(error['loc'][0]) if error['loc'] else 'campo'
            mensaje = error['msg']
            errores.append(f"{campo.capitalize()}: {mensaje}")
        
        # Creamos un objeto residente temporal para mostrar en el formulario
        residente_temp = ResidenteDB(
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
        
        # Mostramos el formulario con los errores
        return templates.TemplateResponse(
            "pages/editar_residente.html",
            {
                "request": request,
                "residente": residente_temp,
                "errores": errores
            },
            status_code=422
        )
