# Procesamiento de datos
# -----------------------------------------------------------------------
import re
import numpy as np
import pandas as pd


# =======================================================================
# FUNCIONES DE LIMPIEZA POR COLUMNA (una por tipo de dato, validadas en el EDA)
# =======================================================================

# -----------------------------------------------------------------------
# Extrae el id numérico de textos como CLI_0572, CLI0023, cli-625 o solo 625
# Todo lo demás (cabeceras repetidas, totales, filas vacías) queda en NaN
# -----------------------------------------------------------------------
def limpiar_id(serie, prefijo):

    return serie.str.strip().str.extract(rf'(?i)^(?:{prefijo}[_-]?)?(\d+)$')[0]


# -----------------------------------------------------------------------
# Convierte fechas escritas en varios formatos en una columna datetime real
# Las fechas inválidas (31/02/2025, 00/00/0000...) quedan en NaT
# -----------------------------------------------------------------------
def limpiar_fecha(serie):

    s = serie.str.strip()
    # Formatos que hay: 2025-08-31, 2025/07/20, 24/03/2025, 05.05.2025, 12-09-25 y July 30, 2025
    formatos = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d.%m.%Y', '%d-%m-%y', '%B %d, %Y']
    resultado = pd.Series(pd.NaT, index=s.index, dtype='datetime64[ns]')
    for f in formatos:
        resultado = resultado.fillna(pd.to_datetime(s, format=f, errors='coerce'))
    return resultado


# -----------------------------------------------------------------------
# Convierte importes escritos de distintas formas (12.345,67 / 12345.67 / 12.345 EUR...) en números
# Sirve para ingresos, deuda total y cuota mensual
# -----------------------------------------------------------------------
def limpiar_importes(serie):

    # Fuera €, EUR, espacios y textos (n/d, Sin ingresos). Dejamos números, coma, punto y el signo menos
    s = serie.str.replace(r'[^\d,.\-]', '', regex=True)
    # Si hay coma es el decimal y los puntos son de miles, como en 3.209,17
    con_coma = s.str.contains(',', na=False)
    s = s.where(~con_coma, s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False))
    # Sin coma: un punto con 3 dígitos detrás es de miles (3.029), con 1 o 2 es decimal (1497.82)
    miles = s.str.match(r'^-?\d{1,3}(\.\d{3})+$', na=False)
    s = s.where(~miles, s.str.replace('.', '', regex=False))
    return pd.to_numeric(s, errors='coerce')


# -----------------------------------------------------------------------
# Quita espacios, junta los espacios repetidos y unifica mayúsculas y minúsculas
# -----------------------------------------------------------------------
def limpiar_texto(serie):

    return serie.str.strip().str.replace(r'\s+', ' ', regex=True).str.title()


# -----------------------------------------------------------------------
# Deja solo los emails válidos (algo antes de la @, algo después y un punto en el dominio)
# -----------------------------------------------------------------------
def validar_email(serie):

    s = serie.str.strip().str.lower()
    patron = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return s.where(s.str.match(patron, na=False))


# -----------------------------------------------------------------------
# Se queda con los 9 últimos dígitos (quita el 34 o el 0034) y solo con móviles válidos
# -----------------------------------------------------------------------
def limpiar_telefono(serie):

    s = serie.str.replace(r'\D', '', regex=True).str[-9:]
    valido = (s.str.len() == 9) & s.str[0].isin(['6', '7'])
    return s.where(valido)


# -----------------------------------------------------------------------
# Códigos postales: se mantienen como texto porque no son valores de operaciones
# -----------------------------------------------------------------------
def limpiar_cp(serie):

    s = serie.str.replace(r'\D', '', regex=True)
    # Los vacíos o con más de 5 dígitos no se pueden arreglar, a NaN
    s = s.where(s.str.len().between(1, 5))
    # A los de menos de 5 les faltan ceros delante, 8151 pasa a 08151
    return s.str.zfill(5)


# -----------------------------------------------------------------------
# Unifica todas las formas de decir sí o no en una columna booleana
# -----------------------------------------------------------------------
def limpiar_aval(serie):

    s = serie.str.strip().str.lower()
    # Todas las formas de decir sí y no que hay en la columna
    mapa = {'true': True, 'si': True, 'sí': True, 's': True, '1': True,
            'false': False, 'no': False, 'n': False, '0': False}
    return s.map(mapa).astype('boolean')


# -----------------------------------------------------------------------
# Unifica los separadores de la lista de acreedores (; , / | y la palabra "y") en "; "
# -----------------------------------------------------------------------
def limpiar_acreedores(serie):

    s = serie.str.strip().str.replace(r'\s+', ' ', regex=True)
    return s.str.replace(r'\s*[;,/|]\s*|\s+y\s+', '; ', regex=True)


# -----------------------------------------------------------------------
# Correcciones encontradas en el EDA para las columnas categóricas
# -----------------------------------------------------------------------
CORRECCIONES_OFICINA = {
    'Malaga': 'Málaga',
    'Sevila': 'Sevilla',
    'Barna': 'Barcelona',
    'València': 'Valencia',
    'N/D': np.nan,
    '-': np.nan,
}

CORRECCIONES_CANAL = {
    'Seo Organico': 'Seo Orgánico',
    'Telefono / Directo': 'Teléfono / Directo',
    'Recomendacion': 'Recomendación',
    'Gogle Ads': 'Google Ads',
    'Rrss': 'Redes Sociales',
    'N/D': np.nan,
    '-': np.nan,
}

CORRECCIONES_ESTADO = {
    'Aceptado/En Negociacion': 'Aceptado / En Negociación',
    'Aceptado / En Negociacion': 'Aceptado / En Negociación',
    'Aceptado': 'Aceptado / En Negociación',
    'Activo': 'Plan Activo',
    'Estudio': 'En Estudio',
    'Cancelado': 'Cancelado Con Éxito',
    'Cancelado Con Exito': 'Cancelado Con Éxito',
    '-': np.nan,
    'N/D': np.nan,
}


def limpiar_oficina(serie):

    return serie.replace(CORRECCIONES_OFICINA)


def limpiar_canal(serie):

    return serie.replace(CORRECCIONES_CANAL)


def limpiar_estado(serie):

    return limpiar_texto(serie).replace(CORRECCIONES_ESTADO)


# -----------------------------------------------------------------------
# Objetivo de las oficinas: unos vienen como 0.30 y otros como 30. Todo en porcentaje
# -----------------------------------------------------------------------
def limpiar_objetivo(serie):

    s = serie.str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    n = pd.to_numeric(s, errors='coerce')
    return n.where(n > 1, n * 100).round(1)


# -----------------------------------------------------------------------
# Iguala los nombres de columna: EXPEDIENTE-ID pasa a ExpedienteId (se usa durante la limpieza)
# -----------------------------------------------------------------------
def limpiar_columnas(columnas):

    return (columnas.str.replace('-', ' ', regex=False)
                    .str.strip()
                    .str.title()
                    .str.replace(' ', '', regex=False))


# -----------------------------------------------------------------------
# Pasa los nombres finales de columna a snake_case, el mismo estilo de la base de datos:
# ClienteId pasa a cliente_id
# -----------------------------------------------------------------------
def a_snake_case(df):

    df = df.copy()
    df.columns = [re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', col).lower() for col in df.columns]
    return df


# =======================================================================
# FUNCIONES DE LIMPIEZA POR TABLA (aplican las decisiones validadas en el EDA)
# =======================================================================

# -----------------------------------------------------------------------
# Tabla de oficinas
# -----------------------------------------------------------------------
def limpiar_dataframe_oficinas(df_oficinas_raw):

    df = df_oficinas_raw.rename(columns={
        'nombre oficina': 'NombreOficina',
        'objetivo_conversion_%': 'ObjetivoConversionPct',
        'Fecha Apertura': 'FechaAperturaOficina',
    })

    df['NombreOficina'] = limpiar_oficina(limpiar_texto(df['NombreOficina']))
    df['Responsable'] = limpiar_texto(df['Responsable'])
    df['ObjetivoConversionPct'] = limpiar_objetivo(df['ObjetivoConversionPct'])
    df['FechaAperturaOficina'] = limpiar_fecha(df['FechaAperturaOficina'])

    # Primero los duplicados exactos. Después, si una oficina aparece dos veces con distinto
    # responsable, nos quedamos con la primera (decisión tomada en el EDA)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset='NombreOficina', keep='first')
    df = df.reset_index(drop=True)

    # Clave primaria de la tabla maestra
    df['oficina_id'] = range(1, len(df) + 1)

    return df


# -----------------------------------------------------------------------
# Tabla de clientes
# -----------------------------------------------------------------------
def limpiar_dataframe_clientes(df_clientes_raw):

    df = df_clientes_raw.copy()

    # Filas duplicadas exactas
    df = df.drop_duplicates()

    # Id de cliente: la cabecera repetida, la fila de "total" y las filas vacías quedan en NaN y se quitan
    antes = len(df)
    df['ClienteId'] = limpiar_id(df['ClienteId'], 'cli')
    df = df.dropna(subset=['ClienteId'])
    df['ClienteId'] = df['ClienteId'].astype(int)
    print(f"Filas eliminadas por ClienteId no válido: {antes - len(df)}")

    # Columnas de texto
    cols_texto = ['NombreCompleto', 'CanalCaptacion', 'DepartamentoOficina']
    df[cols_texto] = df[cols_texto].apply(limpiar_texto)

    df['Email'] = validar_email(df['Email'])
    df['Telefono'] = limpiar_telefono(df['Telefono'])
    df['CodigoPostal'] = limpiar_cp(df['CodigoPostal'])

    # Los ingresos negativos no tienen sentido como ingreso mensual: se consideran un error y se pasan a positivo
    df['IngresosMensuales'] = limpiar_importes(df['IngresosMensuales']).abs()

    df['TieneAval'] = limpiar_aval(df['TieneAval'])
    df['FechaEntrada'] = limpiar_fecha(df['FechaEntrada'])
    df['DepartamentoOficina'] = limpiar_oficina(df['DepartamentoOficina'])
    df['CanalCaptacion'] = limpiar_canal(df['CanalCaptacion'])

    # Mismo ClienteId con distintos datos de contacto. Decisión tomada en el EDA:
    # las filas cuyo email empieza por "nuevo." son las artificiales, así que nos quedamos con la otra
    df['_relleno'] = df['Email'].str.startswith('nuevo.', na=False)
    df = (df.sort_values('_relleno', kind='stable')
            .drop_duplicates(subset='ClienteId', keep='first')
            .drop(columns='_relleno')
            .sort_index())

    return df


# -----------------------------------------------------------------------
# Tabla de expedientes
# -----------------------------------------------------------------------
def limpiar_dataframe_expedientes(df_expedientes_raw, ids_clientes_validos):

    df = df_expedientes_raw.copy()

    # Nombres de columna (EXPEDIENTE-ID pasa a ExpedienteId) y filas duplicadas exactas
    df.columns = limpiar_columnas(df.columns)
    df = df.drop_duplicates()

    # Id de expediente y de cliente
    antes = len(df)
    ids_exp = limpiar_id(df['ExpedienteId'], 'exp')
    ids_cli = limpiar_id(df['ClienteId'], 'cli')
    df['ExpedienteId'] = ids_exp
    df['ClienteId'] = ids_cli
    df = df.dropna(subset=['ExpedienteId'])
    df['ExpedienteId'] = df['ExpedienteId'].astype(int)
    df['ClienteId'] = df['ClienteId'].astype('Int64')
    print(f"Filas eliminadas por ExpedienteId no válido: {antes - len(df)}")

    df['FechaApertura'] = limpiar_fecha(df['FechaApertura'])

    # La misma función de los ingresos sirve para los euros de estas dos columnas
    df['DeudaTotal'] = limpiar_importes(df['DeudaTotal'])
    df['CuotaMensualPropuesta'] = limpiar_importes(df['CuotaMensualPropuesta'])

    df['NumAcreedores'] = pd.to_numeric(df['NumAcreedores'], errors='coerce').astype('Int64')
    df['Acreedores'] = limpiar_acreedores(df['Acreedores'])
    df['EstadoExpediente'] = limpiar_estado(df['EstadoExpediente'])

    # Mismo ExpedienteId con datos distintos: nos quedamos con el primero
    # PENDIENTE (EDA): confirmar esta decisión, en el EDA solo se comprobó, no se aplicó
    antes = len(df)
    df = df.drop_duplicates(subset='ExpedienteId', keep='first')
    print(f"Filas eliminadas por ExpedienteId repetido: {antes - len(df)}")

    # Los expedientes cuyo cliente no existe en la tabla de clientes (o que no tienen cliente)
    # se eliminan para mantener la clave foránea consistente
    antes = len(df)
    df = df[df['ClienteId'].isin(ids_clientes_validos)]
    print(f"Filas eliminadas porque su cliente no existe: {antes - len(df)}")

    # PENDIENTE (EDA): deudas y cuotas negativas o a cero, y valores extremos, siguen en los datos
    # PENDIENTE (EDA): fechas de apertura anteriores a la entrada del cliente o en el futuro

    return df


# -----------------------------------------------------------------------
# Genera las tablas maestras de canales y estados
# -----------------------------------------------------------------------
def construir_tablas_maestras(df_clientes_limpio, df_expedientes_limpio):

    # Tabla maestra de canales
    canales_unicos = sorted(df_clientes_limpio["CanalCaptacion"].dropna().unique())
    df_canales = pd.DataFrame({
        "canal_id": range(1, len(canales_unicos) + 1),
        "canal_nombre": canales_unicos
    })

    # Tabla maestra de estados
    estados_unicos = sorted(df_expedientes_limpio["EstadoExpediente"].dropna().unique())
    df_estados = pd.DataFrame({
        "estado_id": range(1, len(estados_unicos) + 1),
        "estado_nombre": estados_unicos
    })

    return df_canales, df_estados


# -----------------------------------------------------------------------
# Proceso completo de transformación para la base de datos relacional
# -----------------------------------------------------------------------
def transformar_datos_deuda(df_clientes_raw, df_expedientes_raw, df_oficinas_raw):

    # Limpia los tres DataFrames principales
    df_oficinas = limpiar_dataframe_oficinas(df_oficinas_raw)
    df_clientes_limpio = limpiar_dataframe_clientes(df_clientes_raw)
    df_expedientes_limpio = limpiar_dataframe_expedientes(df_expedientes_raw, df_clientes_limpio["ClienteId"])

    # Construye las tablas maestras
    df_canales, df_estados = construir_tablas_maestras(df_clientes_limpio, df_expedientes_limpio)

    # Vuelve a añadir las claves foráneas (IDs) al DataFrame de clientes
    df_clientes_ext = pd.merge(df_clientes_limpio, df_canales, left_on="CanalCaptacion", right_on="canal_nombre", how="left")
    df_clientes_ext = pd.merge(df_clientes_ext, df_oficinas[["oficina_id", "NombreOficina"]],
                               left_on="DepartamentoOficina", right_on="NombreOficina", how="left")

    # Vuelve a añadir las claves foráneas (IDs) al DataFrame de expedientes
    df_expedientes_ext = pd.merge(df_expedientes_limpio, df_estados, left_on="EstadoExpediente", right_on="estado_nombre", how="left")

    # Selección final de columnas
    columnas_clientes = [
        "ClienteId", "NombreCompleto", "FechaEntrada", "canal_id", "oficina_id",
        "CodigoPostal", "Email", "Telefono", "IngresosMensuales", "TieneAval"
    ]
    columnas_expedientes = [
        "ExpedienteId", "ClienteId", "FechaApertura", "DeudaTotal", "NumAcreedores",
        "Acreedores", "CuotaMensualPropuesta", "estado_id"
    ]
    df_clientes_final = df_clientes_ext[columnas_clientes].copy()
    df_expedientes_final = df_expedientes_ext[columnas_expedientes].copy()

    # Claves foráneas como enteros que admiten nulos
    df_clientes_final[["canal_id", "oficina_id"]] = df_clientes_final[["canal_id", "oficina_id"]].astype("Int64")
    df_expedientes_final["estado_id"] = df_expedientes_final["estado_id"].astype("Int64")

    # Nombres de columna finales en snake_case, como en los esquemas de la base de datos
    columnas_oficinas = ["oficina_id", "NombreOficina", "Responsable", "ObjetivoConversionPct", "FechaAperturaOficina"]
    df_oficinas_final = a_snake_case(df_oficinas[columnas_oficinas])
    df_clientes_final = a_snake_case(df_clientes_final)
    df_expedientes_final = a_snake_case(df_expedientes_final)

    return df_oficinas_final, df_canales, df_estados, df_clientes_final, df_expedientes_final
