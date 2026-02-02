from dotenv import load_dotenv, find_dotenv
import os
import mysql.connector
from typing import List, Dict, Any, cast
from mysql.connector.cursor import MySQLCursorDict  # opción C si la prefieres

# Carga .env desde la raíz
load_dotenv(find_dotenv())

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),        # <— corregidos nombres
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "clientes_db"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset="utf8mb4"
    )

def fetch_all_clientes() -> List[Dict[str, Any]]:
    """
    Ejecuta SELECT * FROM clientes y devuelve una lista de dicts.
    """
    conn = None
    try:
        conn = get_connection()
        # Opción C (anotación explícita del cursor):
        cur: MySQLCursorDict
        cur = conn.cursor(dictionary=True)  # type: ignore[assignment]
        try:
            cur.execute(
                "SELECT id, nombre, apellido, email, telefono, direccion FROM clientes;"
            )
            # Opción A: cast para contentar al type checker
            rows = cast(List[Dict[str, Any]], cur.fetchall())
            return rows

            # Opción B alternativa (sin cast):
            # return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def insert_cliente(
    nombre: str, 
    apellido: str, 
    email: str, 
    telefono: str | None = None, 
    direccion: str | None = None
) -> int:
    """
    Inserta un nuevo cliente en la base de datos.
    Retorna el ID del cliente insertado.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO clientes (nombre, apellido, email, telefono, direccion)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nombre, apellido, email, telefono, direccion)
            )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def delete_cliente(cliente_id: int) -> bool:
    """
    Elimina un cliente de la base de datos por su ID.
    Retorna True si se eliminó correctamente, False si no se encontró.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM clientes WHERE id = %s",
                (cliente_id,)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def fetch_cliente_by_id(cliente_id: int) -> Dict[str, Any] | None:
    """
    Obtiene un cliente por su ID.
    Retorna un dict con los datos del cliente o None si no existe.
    """
    conn = None
    try:
        conn = get_connection()
        cur: MySQLCursorDict
        cur = conn.cursor(dictionary=True)  # type: ignore[assignment]
        try:
            cur.execute(
                "SELECT id, nombre, apellido, email, telefono, direccion FROM clientes WHERE id = %s",
                (cliente_id,)
            )
            result = cur.fetchone()
            return dict(result) if result else None
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()


def update_cliente(
    cliente_id: int,
    nombre: str,
    apellido: str,
    email: str,
    telefono: str | None = None,
    direccion: str | None = None
) -> bool:
    """
    Actualiza los datos de un cliente existente.
    Retorna True si se actualizó correctamente, False si no se encontró.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE clientes 
                SET nombre = %s, apellido = %s, email = %s, telefono = %s, direccion = %s
                WHERE id = %s
                """,
                (nombre, apellido, email, telefono, direccion, cliente_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    finally:
        if conn:
            conn.close()
