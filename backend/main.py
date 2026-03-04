from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import date
import mysql.connector
from mysql.connector.errors import IntegrityError, DatabaseError
import re

from backend.database import (
    fetch_all_residentes,
    insert_residente,
    delete_residente,
    fetch_residente_by_id,
    update_residente
)


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
    def validar_nombre_apellido(cls, value: str) -> str:
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

    @field_validator('fecha_nacimiento')
    @classmethod
    def validar_fecha_nacimiento(cls, value: date) -> date:
        if value > date.today():
            raise ValueError('La fecha de nacimiento no puede ser futura')

        edad_aprox = (date.today() - value).days // 365
        if edad_aprox > 150:
            raise ValueError('La fecha de nacimiento no es válida')

        return value

    @field_validator('pasaporte')
    @classmethod
    def validar_pasaporte(cls, value: str) -> str:
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

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, value: Optional[str]) -> Optional[str]:
        if not value or (isinstance(value, str) and value.strip() == ''):
            raise ValueError('El teléfono es obligatorio')

        value = value.strip()
        telefono_limpio = re.sub(r'[\s\-\(\)]', '', value)

        if len(telefono_limpio) < 7:
            raise ValueError('El teléfono debe tener al menos 7 dígitos')
        
        if len(telefono_limpio) > 15:
            raise ValueError('El teléfono no puede exceder 15 dígitos')

        if not re.match(r'^\+?\d{7,15}$', telefono_limpio):
            raise ValueError('Formato de teléfono inválido. Solo se permiten dígitos, +, - y espacios')

        return value

    @field_validator('direccion')
    @classmethod
    def validar_direccion(cls, value: Optional[str]) -> Optional[str]:
        if not value or (isinstance(value, str) and value.strip() == ''):
            raise ValueError('La dirección es obligatoria')

        value = value.strip()

        if len(value) > 255:
            raise ValueError('La dirección no puede exceder 255 caracteres')

        return value

    @field_validator('ocupacion')
    @classmethod
    def validar_ocupacion(cls, value: Optional[str]) -> Optional[str]:
        if not value or (isinstance(value, str) and value.strip() == ''):
            raise ValueError('La ocupación es obligatoria')

        value = value.strip()

        if len(value) > 100:
            raise ValueError('La ocupación no puede exceder 100 caracteres')

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-]+$', value):
            raise ValueError('La ocupación solo puede contener letras, espacios, puntos y guiones')

        return value.title()

    @field_validator('estado_civil')
    @classmethod
    def validar_estado_civil(cls, value: Optional[str]) -> Optional[str]:
        if not value or (isinstance(value, str) and value.strip() == ''):
            raise ValueError('El estado civil es obligatorio')

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


class ResidenteCreate(ResidenteBase):
    pass


class ResidenteUpdate(ResidenteBase):
    pass


class ResidenteOut(ResidenteBase):
    id: int


class ResidenteOutDB(BaseModel):
    """Modelo sin validadores para lectura desde BD (permite datos históricos)"""
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


class DeleteResponse(BaseModel):
    mensaje: str


app = FastAPI(title="Sistema de Gestion de Residentes - Embajada")

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(mysql.connector.Error)
async def database_exception_handler(request, exc: mysql.connector.Error):
    import traceback
    print(f"Database error: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error de base de datos: {str(exc)}"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador personalizado para errores de validación de Pydantic"""
    errors = exc.errors()
    
    # Intentar crear un mensaje legible a partir de los errores
    error_messages = []
    for error in errors:
        field = '.'.join(str(x) for x in error['loc'][1:])  # Omitir 'body'
        msg = error.get('msg', 'Error de validación')
        
        # Hacer el mensaje más legible
        if 'string_type' in msg or 'str' in msg:
            msg = f"El campo '{field}' debe ser texto"
        elif 'email' in msg.lower() or 'type=email' in str(error):
            msg = f"El correo electrónico '{field}' no es válido"
        elif 'int_type' in msg or 'int_parsing' in msg:
            msg = f"El campo '{field}' debe ser un número entero"
        elif 'date' in msg.lower():
            msg = f"El campo '{field}' debe ser una fecha válida (formato: YYYY-MM-DD)"
        else:
            msg = f"{field}: {error.get('msg', 'Error de validación')}"
        
        error_messages.append(msg)
    
    detail = error_messages[0] if error_messages else "Error de validación en los datos enviados"
    
    return JSONResponse(
        status_code=422,
        content={"detail": detail}
    )


def map_rows_to_residentes(rows: List[dict]) -> List[ResidenteOutDB]:
    return [ResidenteOutDB(**row) for row in rows]


@app.get("/", response_model=dict)
def health_check():
    return {"status": "ok"}


@app.get("/residentes", response_model=List[ResidenteOutDB])
def list_residentes():
    rows = fetch_all_residentes()
    return map_rows_to_residentes(rows)


@app.get("/residentes/{residente_id}", response_model=ResidenteOutDB)
def get_residente(residente_id: int):
    residente = fetch_residente_by_id(residente_id)
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return ResidenteOutDB(**residente)


@app.post("/residentes", response_model=ResidenteOutDB, status_code=201)
def create_residente(residente: ResidenteCreate):
    try:
        residente_id = insert_residente(
            residente.nombre,
            residente.apellido,
            str(residente.fecha_nacimiento),
            residente.pasaporte,
            residente.email,
            residente.telefono,
            residente.direccion,
            residente.ocupacion,
            residente.estado_civil
        )

        created = fetch_residente_by_id(residente_id)
        if created:
            return ResidenteOutDB(**created)

        payload = residente.model_dump()
        return ResidenteOutDB(id=residente_id, **payload)
    
    except IntegrityError as e:
        # Error 1062 es duplicate entry
        if "1062" in str(e) or "Duplicate entry" in str(e):
            # Extraer el campo del error
            if "email" in str(e).lower():
                raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado en el sistema")
            elif "pasaporte" in str(e).lower():
                raise HTTPException(status_code=400, detail="El número de pasaporte ya está registrado")
            else:
                raise HTTPException(status_code=400, detail="Este registro ya existe en el sistema")
        else:
            raise HTTPException(status_code=400, detail=f"Error de validación: {str(e)}")
    
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@app.put("/residentes/{residente_id}", response_model=ResidenteOutDB)
def update_residente_endpoint(residente_id: int, residente: ResidenteUpdate):
    try:
        actualizado = update_residente(
            residente_id,
            residente.nombre,
            residente.apellido,
            str(residente.fecha_nacimiento),
            residente.pasaporte,
            residente.email,
            residente.telefono,
            residente.direccion,
            residente.ocupacion,
            residente.estado_civil
        )

        if not actualizado:
            raise HTTPException(status_code=404, detail="Residente no encontrado")

        updated = fetch_residente_by_id(residente_id)
        if updated:
            return ResidenteOutDB(**updated)

        payload = residente.model_dump()
        return ResidenteOutDB(id=residente_id, **payload)
    
    except IntegrityError as e:
        # Error 1062 es duplicate entry
        if "1062" in str(e) or "Duplicate entry" in str(e):
            # Extraer el campo del error
            if "email" in str(e).lower():
                raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado en el sistema")
            elif "pasaporte" in str(e).lower():
                raise HTTPException(status_code=400, detail="El número de pasaporte ya está registrado")
            else:
                raise HTTPException(status_code=400, detail="Este registro ya existe en el sistema")
        else:
            raise HTTPException(status_code=400, detail=f"Error de validación: {str(e)}")
    
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@app.delete("/residentes/{residente_id}", response_model=DeleteResponse)
def delete_residente_endpoint(residente_id: int):
    eliminado = delete_residente(residente_id)

    if not eliminado:
        raise HTTPException(status_code=404, detail="Residente no encontrado")

    return DeleteResponse(mensaje="Residente eliminado exitosamente")
                                    