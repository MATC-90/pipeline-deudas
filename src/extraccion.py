# Librerías
# -----------------------------------------------------------------------
import pandas as pd
from pathlib import Path


# -----------------------------------------------------------------------
# Lee los tres CSV en bruto. Todas las columnas se leen como texto (dtype=str)
# para que ningún valor se convierta solo antes de la limpieza
# -----------------------------------------------------------------------
def extraer_datos_brutos(ruta_raw="raw"):

    ruta_raw = Path(ruta_raw)

    # Clientes: exportados desde Excel (separador punto y coma y codificación de Windows)
    df_clientes_raw = pd.read_csv(ruta_raw / "clientes_raw.csv", sep=";", encoding="cp1252", dtype=str)

    # Expedientes y oficinas: separador coma, UTF-8
    df_expedientes_raw = pd.read_csv(ruta_raw / "expedientes_raw.csv", dtype=str)
    df_oficinas_raw = pd.read_csv(ruta_raw / "oficinas_raw.csv", dtype=str)

    return df_clientes_raw, df_expedientes_raw, df_oficinas_raw
