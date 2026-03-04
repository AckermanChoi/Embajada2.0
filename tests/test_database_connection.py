"""
Script de test para verificar la conexión a la base de datos.
Prueba que la función get_connection() de database.py funcione correctamente
con la configuración del archivo .env
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar app
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.database import get_connection
import mysql.connector
from mysql.connector import Error


def test_connection():
    """
    Prueba la conexión a la base de datos usando get_connection().
    Verifica que:
    1. La conexión se establece correctamente
    2. Las credenciales del .env son válidas
    3. La base de datos especificada existe y es accesible
    """
    print("=" * 60)
    print("TEST: Verificación de conexión a la base de datos")
    print("=" * 60)
    
    conn = None
    try:
        print("\n[1] Intentando establecer conexión...")
        conn = get_connection()
        
        if conn is None:
            print("❌ ERROR: get_connection() retornó None")
            return False
        
        if not conn.is_connected():
            print("❌ ERROR: La conexión no está activa")
            return False
        
        print("✅ Conexión establecida exitosamente")
        
        # Obtener información de la conexión
        print("\n[2] Información de la conexión:")
        db_info = conn.get_server_info()
        print(f"   - Versión del servidor MySQL: {db_info}")
        
        # Verificar la base de datos actual
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        print(f"   - Base de datos conectada: {db_name[0]}")
        cursor.close()
        
        # Probar una consulta simple
        print("\n[3] Probando consulta simple...")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test;")
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0] == 1:
            print("✅ Consulta de prueba ejecutada correctamente")
        else:
            print("❌ ERROR: La consulta de prueba falló")
            return False
        
        # Verificar que la tabla residentes existe
        print("\n[4] Verificando tabla 'residentes'...")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'residentes';")
        table_exists = cursor.fetchone()
        cursor.close()
        
        if table_exists:
            print("✅ La tabla 'residentes' existe en la base de datos")
            
            # Verificar la estructura de la tabla
            print("\n[5] Verificando estructura de la tabla 'residentes'...")
            cursor = conn.cursor()
            cursor.execute("DESCRIBE residentes;")
            columns = cursor.fetchall()
            cursor.close()
            
            expected_columns = ['id', 'nombre', 'apellido', 'fecha_nacimiento', 
                              'pasaporte', 'email', 'telefono', 'direccion', 
                              'ocupacion', 'estado_civil']
            actual_columns = [col[0] for col in columns]
            
            if all(col in actual_columns for col in expected_columns):
                print("✅ La estructura de la tabla es correcta")
                print(f"   Columnas: {', '.join(actual_columns)}")
            else:
                print("⚠️  ADVERTENCIA: La estructura de la tabla no coincide")
                print(f"   Esperado: {', '.join(expected_columns)}")
                print(f"   Actual: {', '.join(actual_columns)}")
            
            # Contar registros
            print("\n[6] Verificando datos en la tabla...")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM residentes;")
            count = cursor.fetchone()
            cursor.close()
            
            if count and count[0] > 0:
                print(f"✅ La tabla contiene {count[0]} registro(s)")
            else:
                print("⚠️  ADVERTENCIA: La tabla está vacía")
                print("   Considera insertar datos de ejemplo")
        else:
            print("⚠️  ADVERTENCIA: La tabla 'residentes' no existe")
            print("   Ejecuta el script docs/init_db.sql para inicializar la base de datos")
        
        print("\n" + "=" * 60)
        print("✅ RESULTADO: Todas las pruebas pasaron correctamente")
        print("=" * 60)
        return True
        
    except Error as e:
        print(f"\n❌ ERROR de MySQL: {e}")
        print("\nPosibles causas:")
        print("  - Verifica las credenciales en el archivo .env")
        print("  - Asegúrate de que el servidor MySQL esté corriendo")
        print("  - Verifica que la base de datos especificada exista")
        print("  - Comprueba el host y puerto de conexión")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {type(e).__name__}: {e}")
        return False
        
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("\n[INFO] Conexión cerrada correctamente")


def show_env_config():
    """
    Muestra la configuración de conexión desde las variables de entorno
    (sin mostrar la contraseña completa)
    """
    print("\n" + "=" * 60)
    print("CONFIGURACIÓN DE CONEXIÓN (.env)")
    print("=" * 60)
    print(f"DB_HOST:     {os.getenv('DB_HOST', 'localhost')}")
    print(f"DB_USER:     {os.getenv('DB_USER', 'root')}")
    password = os.getenv('DB_PASSWORD', '')
    masked_pwd = '*' * len(password) if password else '<vacío>'
    print(f"DB_PASSWORD: {masked_pwd}")
    print(f"DB_NAME:     {os.getenv('DB_NAME', 'clientes_db')}")
    print(f"DB_PORT:     {os.getenv('DB_PORT', '3306')}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🔍 Script de prueba de conexión a base de datos\n")
    
    # Mostrar configuración
    show_env_config()
    
    # Ejecutar test
    success = test_connection()
    
    # Código de salida
    sys.exit(0 if success else 1)


# ============================================================================
# INSTRUCCIONES PARA EJECUTAR MANUALMENTE
# ============================================================================
#
# Para ejecutar este test desde la consola y verificar que la conexión
# a la base de datos funciona correctamente:
#
# 1. Asegúrate de estar en el directorio raíz del proyecto:
#    cd /ruta/a/tu/proyecto/embajada
#
# 2. Ejecuta el script de test:
#    python tests/test_database_connection.py
#
# 3. Si usas un entorno virtual, actívalo primero:
#    source .venv/bin/activate
#    python tests/test_database_connection.py
#
# RESULTADO ESPERADO:
# - Si la conexión es exitosa: El script mostrará ✅ y retornará código 0
# - Si hay errores: Mostrará ❌ con detalles del error y retornará código 1
#
# NOTA: Asegúrate de que el archivo .env tenga configuradas correctamente
# las variables: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
#
# ============================================================================
