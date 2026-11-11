# Procesamiento de datos
import pandas as pd

# Módulos propios
import src.funciones as fn
import src.db as db
import src.transformacion as tr
import src.extraccion as ext

# Variables de entorno
import os
from dotenv import load_dotenv

load_dotenv()
contrasena_sql = os.getenv("PASS_SQL")



# =======================================================================
# SCRIPT PRINCIPAL DE CARGA (ETL)
# =======================================================================


# -----------------------------------------------------------------------
# 1. EXTRACCIÓN (Extract)
# -----------------------------------------------------------------------
print("Leyendo los archivos CSV en bruto...")

df_clientes_raw, df_expedientes_raw, df_oficinas_raw = ext.extraer_datos_brutos("raw")
print(f"\nExtracción completada: {len(df_clientes_raw)} clientes, "
      f"{len(df_expedientes_raw)} expedientes y {len(df_oficinas_raw)} oficinas en bruto.")


# -----------------------------------------------------------------------
# 2. TRANSFORMACIÓN (Transform)
# -----------------------------------------------------------------------
print("Aplicando la limpieza completa y las transformaciones relacionales...")
df_oficinas, df_canales, df_estados, df_clientes_final, df_expedientes_final = tr.transformar_datos_deuda(
    df_clientes_raw, df_expedientes_raw, df_oficinas_raw
)
print("¡Transformación completada con éxito!")

os.makedirs("clean", exist_ok=True)
df_oficinas.to_csv("clean/oficinas_ETL.csv", index=False, sep=";", encoding="utf-8")
df_canales.to_csv("clean/canales_ETL.csv", index=False, sep=";", encoding="utf-8")
df_estados.to_csv("clean/estados_ETL.csv", index=False, sep=";", encoding="utf-8")
df_clientes_final.to_csv("clean/clientes_ETL.csv", index=False, sep=";", encoding="utf-8")
df_expedientes_final.to_csv("clean/expedientes_ETL.csv", index=False, sep=";", encoding="utf-8")

# -----------------------------------------------------------------------
# 3. CARGA (Load)
# -----------------------------------------------------------------------
print("\n--- Iniciando el proceso de carga en MySQL ---")

# Paso 1: Conexión
conexion = fn.conexion_mysql()

# Paso 2: Creación de la base de datos
fn.crear_base_datos(conexion, db.NOMBRE_BD)

# Paso 3: Creación de las tablas (primero las padre, después las hijas)
print("\nCreando la estructura de las tablas...")
fn.crear_tabla_generica(conexion, db.NOMBRE_BD, db.TABLA_OFICINAS, db.ESQUEMA_OFICINAS)
fn.crear_tabla_generica(conexion, db.NOMBRE_BD, db.TABLA_CANALES, db.ESQUEMA_CANALES)
fn.crear_tabla_generica(conexion, db.NOMBRE_BD, db.TABLA_ESTADOS, db.ESQUEMA_ESTADOS)
fn.crear_tabla_generica(conexion, db.NOMBRE_BD, db.TABLA_CLIENTES, db.ESQUEMA_CLIENTES)
fn.crear_tabla_generica(conexion, db.NOMBRE_BD, db.TABLA_EXPEDIENTES, db.ESQUEMA_EXPEDIENTES)

# Paso 4: Inserción de datos (en el mismo orden que la creación de tablas)
print("\nInsertando los datos en las tablas correspondientes...")
fn.insertar_datos(conexion, db.NOMBRE_BD, db.TABLA_OFICINAS, df_oficinas)
fn.insertar_datos(conexion, db.NOMBRE_BD, db.TABLA_CANALES, df_canales)
fn.insertar_datos(conexion, db.NOMBRE_BD, db.TABLA_ESTADOS, df_estados)
fn.insertar_datos(conexion, db.NOMBRE_BD, db.TABLA_CLIENTES, df_clientes_final)
fn.insertar_datos(conexion, db.NOMBRE_BD, db.TABLA_EXPEDIENTES, df_expedientes_final)

print("\n--- ¡Proceso de carga completado con éxito! ---")
