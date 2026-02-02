from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, EmailStr, field_validator, ValidationError
from typing import Optional, List
import mysql.connector
import re

# Importamos las funciones que consultan/insertan/eliminan en MySQL
from app.database import (
    fetch_all_clientes, 
    insert_cliente, 
    delete_cliente,
    fetch_cliente_by_id,
    update_cliente
)


# Modelo base con validaciones comunes
class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre_apellido(cls, v: str) -> str:
        """Valida que nombre y apellido tengan formato correcto."""
        if not v or not v.strip():
            raise ValueError('El campo no puede estar vacío')
        
        v = v.strip()
        
        if len(v) < 2:
            raise ValueError('Debe tener al menos 2 caracteres')
        
        if len(v) > 50:
            raise ValueError('No puede exceder 50 caracteres')
        
        # Solo letras, espacios, tildes y caracteres especiales del español
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', v):
            raise ValueError('Solo se permiten letras y espacios')
        
        return v.title()  # Capitaliza cada palabra
    
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
        
        if len(v) > 200:
            raise ValueError('La dirección no puede exceder 200 caracteres')
        
        return v


# Modelo para lectura de BD (sin validaciones estrictas, acepta datos históricos)
class ClienteDB(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None


# Modelo para crear cliente (sin ID)
class ClienteCreate(ClienteBase):
    pass


# Modelo para actualizar cliente (sin ID)
class ClienteUpdate(ClienteBase):
    pass


# Modelo completo de Cliente (con ID y validaciones)
class Cliente(ClienteBase):
    id: int


app = FastAPI(title="Monolito Clientes con FastAPI y MySQL")

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


def map_rows_to_clientes(rows: List[dict]) -> List[ClienteDB]:
    """
    Convierte las filas del SELECT * FROM clientes (dict) 
    en objetos ClienteDB (sin validaciones estrictas para datos existentes).
    """
    return [
        ClienteDB(
            id=row["id"],
            nombre=row["nombre"],
            apellido=row["apellido"],
            email=row["email"],
            telefono=row.get("telefono"),
            direccion=row.get("direccion"),
        )
        for row in rows
    ]


# --- GET principal ---
@app.get("/", response_class=HTMLResponse)
def get_index(request: Request):
    # 1️⃣ Obtenemos los datos desde MySQL
    rows = fetch_all_clientes()

    # 2️⃣ Convertimos cada fila a Cliente (valida estructura)
    clientes = map_rows_to_clientes(rows)

    # 3️⃣ Enviamos a la plantilla
    return templates.TemplateResponse(
        "pages/index.html",
        {
            "request": request,
            "clientes": clientes
        }
    )


# --- GET formulario nuevo cliente ---
@app.get("/clientes/nuevo", response_class=HTMLResponse)
def get_nuevo_cliente(request: Request):
    return templates.TemplateResponse(
        "pages/nuevo_cliente.html",
        {
            "request": request,
            "mensaje": None
        }
    )


# --- POST guardar nuevo cliente ---
@app.post("/clientes/nuevo")
def post_nuevo_cliente(
    request: Request,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None)
):
    try:
        # Validamos los datos usando Pydantic
        cliente_data = ClienteCreate(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono if telefono else None,
            direccion=direccion if direccion else None
        )
        
        # Insertamos el cliente en la base de datos
        insert_cliente(
            cliente_data.nombre,
            cliente_data.apellido,
            cliente_data.email,
            cliente_data.telefono,
            cliente_data.direccion
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
            "pages/nuevo_cliente.html",
            {
                "request": request,
                "mensaje": None,
                "errores": errores,
                "nombre": nombre,
                "apellido": apellido,
                "email": email,
                "telefono": telefono,
                "direccion": direccion
            },
            status_code=422
        )


# --- DELETE eliminar cliente ---
@app.delete("/clientes/{cliente_id}")
def delete_cliente_endpoint(cliente_id: int):
    """
    Endpoint para eliminar un cliente por su ID.
    """
    eliminado = delete_cliente(cliente_id)
    
    if not eliminado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return JSONResponse(
        content={"mensaje": "Cliente eliminado exitosamente"},
        status_code=200
    )


# --- GET formulario editar cliente ---
@app.get("/clientes/editar/{cliente_id}", response_class=HTMLResponse)
def get_editar_cliente(request: Request, cliente_id: int):
    """
    Endpoint para mostrar el formulario de edición con datos precargados.
    """
    # Obtenemos los datos del cliente
    cliente_data = fetch_cliente_by_id(cliente_id)
    
    if not cliente_data:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Convertimos a modelo ClienteDB para mostrar en formulario (sin validaciones)
    cliente = ClienteDB(**cliente_data)
    
    return templates.TemplateResponse(
        "pages/editar_cliente.html",
        {
            "request": request,
            "cliente": cliente
        }
    )


# --- POST actualizar cliente ---
@app.post("/clientes/editar/{cliente_id}")
def post_editar_cliente(
    request: Request,
    cliente_id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None)
):
    """
    Endpoint para actualizar los datos de un cliente.
    """
    try:
        # Validamos los datos usando Pydantic
        cliente_data = ClienteUpdate(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono if telefono else None,
            direccion=direccion if direccion else None
        )
        
        # Actualizamos el cliente en la base de datos
        actualizado = update_cliente(
            cliente_id,
            cliente_data.nombre,
            cliente_data.apellido,
            cliente_data.email,
            cliente_data.telefono,
            cliente_data.direccion
        )
        
        if not actualizado:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Redirigimos al inicio para ver el listado actualizado
        return RedirectResponse(url="/", status_code=303)
        
    except ValidationError as e:
        # Extraemos los errores de validación
        errores = []
        for error in e.errors():
            campo = str(error['loc'][0]) if error['loc'] else 'campo'
            mensaje = error['msg']
            errores.append(f"{campo.capitalize()}: {mensaje}")
        
        # Creamos un objeto cliente temporal para mostrar en el formulario
        cliente_temp = ClienteDB(
            id=cliente_id,
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            direccion=direccion
        )
        
        # Mostramos el formulario con los errores
        return templates.TemplateResponse(
            "pages/editar_cliente.html",
            {
                "request": request,
                "cliente": cliente_temp,
                "errores": errores
            },
            status_code=422
        )
