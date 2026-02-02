from dotenv import load_dotenv, find_dotenv
import os
import mysql.connector
from typing import List, Dict, Any, cast
from mysql.connector.cursor import MySQLCursorDict  # opción C si la prefieres

# Carga .env desde la raíz
load_dotenv(find_dotenv())

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "residentes_db"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset="utf8mb4"
    )

def fetch_all_residentes() -> List[Dict[str, Any]]:
    """
    Ejecuta SELECT * FROM residentes y devuelve una lista de dicts.
    """
    conn = None
    try:
        conn = get_connection()
        cur: MySQLCursorDict
        cur = conn.cursor(dictionary=True)  # type: ignore[assignment]
        try:
            cur.execute(
                """SELECT id, nombre, apellido, fecha_nacimiento, pasaporte, 
                   email, telefono, direccion, ocupacion, estado_civil 
                   FROM residentes;"""
            )
            rows = cast(List[Dict[str, Any]], cur.fetchall())
            return rows
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def insert_residente(
    nombre: str, 
    apellido: str,
    fecha_nacimiento: str,
    pasaporte: str,
    email: str,
    telefono: str | None = None, 
    direccion: str | None = None,
    ocupacion: str | None = None,
    estado_civil: str | None = None
) -> int:
    """
    Inserta un nuevo residente en la base de datos.
    Retorna el ID del residente insertado.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO residentes (nombre, apellido, fecha_nacimiento, pasaporte, 
                                       email, telefono, direccion, ocupacion, estado_civil)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre, apellido, fecha_nacimiento, pasaporte, email, telefono, 
                 direccion, ocupacion, estado_civil)
            )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def delete_residente(residente_id: int) -> bool:
    """
    Elimina un residente de la base de datos por su ID.
    Retorna True si se eliminó correctamente, False si no se encontró.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM residentes WHERE id = %s",
                (residente_id,)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def fetch_residente_by_id(residente_id: int) -> Dict[str, Any] | None:
    """
    Obtiene un residente por su ID.
    Retorna un dict con los datos del residente o None si no existe.
    """
    conn = None
    try:
        conn = get_connection()
        cur: MySQLCursorDict
        cur = conn.cursor(dictionary=True)  # type: ignore[assignment]
        try:
            cur.execute(
                """SELECT id, nombre, apellido, fecha_nacimiento, pasaporte, 
                   email, telefono, direccion, ocupacion, estado_civil 
                   FROM residentes WHERE id = %s""",
                (residente_id,)
            )
            result = cur.fetchone()
            return dict(result) if result else None
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def update_residente(
    residente_id: int,
    nombre: str,
    apellido: str,
    fecha_nacimiento: str,
    pasaporte: str,
    email: str,
    telefono: str | None = None,
    direccion: str | None = None,
    ocupacion: str | None = None,
    estado_civil: str | None = None
) -> bool:
    """
    Actualiza los datos de un residente existente.
    Retorna True si se actualizó correctamente, False si no se encontró.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE residentes 
                SET nombre = %s, apellido = %s, fecha_nacimiento = %s, pasaporte = %s,
                    email = %s, telefono = %s, direccion = %s, ocupacion = %s, estado_civil = %s
                WHERE id = %s
                """,
                (nombre, apellido, fecha_nacimiento, pasaporte, email, telefono, 
                 direccion, ocupacion, estado_civil, residente_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()
