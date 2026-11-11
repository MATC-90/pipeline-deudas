# =======================================================================
# IMPORTS PARA LAS FUNCIONES
# =======================================================================

# Procesamiento de datos
# -----------------------------------------------------------------------
import pandas as pd

# Conexión a MySQL
# -----------------------------------------------------------------------
import mysql.connector
from mysql.connector import Error

# Variables de entorno
# -----------------------------------------------------------------------
import os
from dotenv import load_dotenv
load_dotenv()
contrasena_sql = os.getenv("PASS_SQL")

# =======================================================================
# DECORADOR: envoltorio de funciones
# =======================================================================

def requiere_conexion(funcion_original):
    def envoltorio(conexion, *args, **kwargs):
        if conexion is None:
            print(f"Error: no hay conexión activa para ejecutar '{funcion_original.__name__}'")
            return None
        return funcion_original(conexion, *args, **kwargs)
    return envoltorio


# =======================================================================
# FUNCIONES DE MySQL
# =======================================================================

# -----------------------------------------------------------------------
# Establece la conexión con el servidor MySQL local
# -----------------------------------------------------------------------
def conexion_mysql():

    try:
        # Usando el conector de la librería
        conexion = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password=contrasena_sql,  # Usa la contraseña de la variable de entorno local, omitida en GitHub
            # Nota: se va a crear una base de datos nueva, así que aquí no se indica su nombre
        )
        print("Conexión correcta")
        return conexion

    # Gestiona cualquier error de base de datos que ocurra durante la conexión
    except Error as e:
        print(f"Ha ocurrido un error: {e}")


# -----------------------------------------------------------------------
# Crea una base de datos nueva si no existe
# -----------------------------------------------------------------------
@requiere_conexion
def crear_base_datos(conexion, nombre_bd):

    try:
        # Abre el cursor con un gestor de contexto para que se cierre solo
        with conexion.cursor() as cursor:
            consulta = f"CREATE DATABASE IF NOT EXISTS {nombre_bd}"
            # Ejecuta la consulta de creación de la base de datos
            cursor.execute(consulta)
            print("Consulta correcta")

    # Captura cualquier error de ejecución SQL
    except Error as e:
        print(f"Error al crear la base de datos: {e}")


# -----------------------------------------------------------------------
# Función para borrar la base de datos si hace falta
# -----------------------------------------------------------------------
@requiere_conexion
def eliminar_base_datos(conexion, nombre_bd):

    try:
        # Pide confirmación al usuario
        respuesta = input(f"Se va a borrar la base de datos '{nombre_bd}'. ¿Seguro? (S/N):").upper()
        # Solo continúa si se confirma
        if respuesta == "S":
            with conexion.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS {nombre_bd}")
                conexion.commit()
                print(f"Base de datos {nombre_bd} eliminada correctamente")
        else:
            # Cualquier otra respuesta cancela el borrado
            print("Operación cancelada")

    # Captura posibles errores de MySQL
    except Error as e:
        print(f"Error al eliminar la base de datos: {e}")


# -----------------------------------------------------------------------
# Crea una tabla genérica en la base de datos indicada si no existe
# -----------------------------------------------------------------------
@requiere_conexion
def crear_tabla_generica(conexion, nombre_bd, nombre_tabla, esquema_tabla):

    try:
        # Abre el cursor con un gestor de contexto para que se cierre solo
        with conexion.cursor() as cursor:
            cursor.execute(f"USE {nombre_bd};")
            # Define la consulta SQL de la tabla genérica
            consulta = f''' CREATE TABLE IF NOT EXISTS {nombre_tabla} ({esquema_tabla});'''
            # Ejecuta la consulta de creación de la tabla
            cursor.execute(consulta)
            print("Consulta de creación correcta")

    # Captura cualquier error de ejecución SQL
    except Error as e:
        print(f"Error al crear la tabla: {e}")


# -----------------------------------------------------------------------
# Función para borrar tablas si hace falta
# -----------------------------------------------------------------------
@requiere_conexion
def eliminar_tabla(conexion, nombre_bd, nombre_tabla):

    try:

        # Comprueba si el usuario confirma la operación
        respuesta = input(f"Se va a borrar la tabla '{nombre_tabla}'. ¿Seguro? (S/N):").upper()
        if respuesta == "S":
            # Abre el cursor con un gestor de contexto para que se cierre solo
            with conexion.cursor() as cursor:
                # Selecciona la base de datos pasada como argumento
                cursor.execute(f"USE {nombre_bd};")
                # Define la consulta SQL para borrar la tabla si existe
                consulta = f'''DROP TABLE IF EXISTS {nombre_tabla}'''
                # Ejecuta la consulta de borrado
                cursor.execute(consulta)
                conexion.commit()
                print("Tabla eliminada correctamente")
        else:
            print("Operación cancelada")

    # Captura cualquier error de ejecución SQL
    except Error as e:
        print(f"Error al eliminar la tabla: {e}")


# -----------------------------------------------------------------------
# Inserta los datos de un DataFrame limpio en la tabla correspondiente
# -----------------------------------------------------------------------
@requiere_conexion
def insertar_datos(conexion, nombre_bd, nombre_tabla, df):

    try:
        # Sustituye los nulos de pandas (NaN, pd.NA, NaT) por None de Python,
        # porque mysql-connector no puede convertir los tipos nulos nativos de pandas
        # (por ejemplo, pd.NA de las columnas Int64 da el error "NAType cannot be converted")
        df_saneado = df.astype(object).where(df.notna(), None)

        # Convierte las filas del DataFrame en una lista de tuplas
        valores = df_saneado.values.tolist()

        # Generación dinámica de la consulta SQL según las columnas del DataFrame
        columnas = ", ".join(df.columns)
        marcadores = ", ".join(["%s"] * len(df.columns))

        consulta = f"INSERT INTO {nombre_tabla} ({columnas}) VALUES ({marcadores})"

        with conexion.cursor() as cursor:
            cursor.execute(f"USE {nombre_bd};")
            # Inserta los registros fila a fila con execute() parametrizado.

            for fila in valores:
                cursor.execute(consulta, fila)
            conexion.commit()
            print(f"Inserción correcta: {len(valores)} registros añadidos a la tabla '{nombre_tabla}'.")

    # Captura errores de ejecución SQL
    except Error as e:
        print(f"Error al insertar datos en la tabla {nombre_tabla}: {e}")
