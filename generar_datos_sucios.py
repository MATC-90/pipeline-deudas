#!/usr/bin/env python3
"""
GENERADOR DE DATOS SUCIOS (ficticio) - sector gestion de deudas

Crea la carpeta raw/ con 3 CSV para practicar un ETL:
    raw/clientes_raw.csv     (separador ';', codificacion cp1252)
    raw/expedientes_raw.csv  (separador ',', codificacion utf-8)
    raw/oficinas_raw.csv     (separador ',', codificacion utf-8)


Requisitos:  pip install pandas numpy
Uso:         python generar_datos_sucios.py
"""
import json
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

OUT = Path("raw")
OUT.mkdir(exist_ok=True)

N_CLIENTES = 800
N_EXPEDIENTES = 1000
control = {}

NULOS = [None, "", "N/A", "null", "NULL", "-", "n/d", "NaN"]


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def pick(lista, p=None):
    return lista[int(rng.choice(len(lista), p=p))]


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def variante_texto(s):
    """Devuelve el texto tal cual o con mayusculas, espacios o tildes alterados."""
    r = rng.random()
    if r < 0.55:
        return s
    if r < 0.65:
        return s.upper()
    if r < 0.75:
        return s.lower()
    if r < 0.82:
        return s + " "
    if r < 0.88:
        return " " + s
    if r < 0.95:
        return sin_tildes(s)
    return s.replace(" ", "  ")


def inyectar_nulos(valores, frac, nombre):
    """Sustituye una fraccion de valores por distintas formas de 'nulo'."""
    vals = list(valores)
    idx = rng.choice(len(vals), size=int(len(vals) * frac), replace=False)
    for i in idx:
        vals[i] = pick(NULOS)
    control[f"nulos_{nombre}"] = int(len(idx))
    return vals


def fmt_id(i, prefijo):
    r = rng.random()
    if r < 0.70:
        return f"{prefijo}_{i:04d}"
    if r < 0.80:
        return f"{prefijo.lower()}-{i}"
    if r < 0.90:
        return f"{prefijo}{i:04d}"
    return str(i) if prefijo == "CLI" else f"{prefijo}_{i}"


def fmt_fecha(d):
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%y", "%Y/%m/%d", "%d.%m.%Y", "%B %d, %Y"]
    p = [0.40, 0.30, 0.10, 0.08, 0.07, 0.05]
    return d.strftime(pick(formatos, p))


def fmt_importe(x):
    """Importe escrito de formas distintas (12345 / 12.345 / 12.345,67 / 12345.67 / con simbolo)."""
    entero = f"{int(x):,}".replace(",", ".")
    r = rng.random()
    if r < 0.30:
        return str(int(x))
    if r < 0.50:
        return entero
    if r < 0.65:
        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if r < 0.75:
        return f"{x:.2f}"
    if r < 0.85:
        return entero + " \u20ac"
    if r < 0.92:
        return "\u20ac " + str(int(x))
    return f"{int(x)} EUR"


def fechas_invalidas(valores, frac, nombre):
    vals = list(valores)
    idx = rng.choice(len(vals), size=int(len(vals) * frac), replace=False)
    malas = ["31/02/2025", "00/00/0000", "2025-13-01", "sin fecha", "32-01-25"]
    for i in idx:
        vals[i] = pick(malas)
    control[f"fechas_invalidas_{nombre}"] = int(len(idx))
    return vals


def fila_basura(df, cabecera):
    """Inserta una cabecera repetida, una fila vacia y una fila de total, como en un Excel exportado."""
    df = df.reset_index(drop=True)
    cab = pd.DataFrame([dict(zip(df.columns, df.columns))])
    vacia = pd.DataFrame([{c: "" for c in df.columns}])
    total = {c: "" for c in df.columns}
    total[df.columns[0]] = cabecera
    total[df.columns[1]] = f"{len(df)} registros"
    pos_cab, pos_vacia = len(df) // 2, (len(df) * 3) // 4
    df = pd.concat([df.iloc[:pos_cab], cab, df.iloc[pos_cab:pos_vacia], vacia,
                    df.iloc[pos_vacia:], pd.DataFrame([total])], ignore_index=True)
    control["filas_basura_" + cabecera.lower()] = 3
    return df


# ----------------------------------------------------------------------
# Catalogos
# ----------------------------------------------------------------------
NOMBRES = ["Mar\u00eda", "Jos\u00e9", "Antonio", "Carmen", "Manuel", "Laura", "Francisco", "Luc\u00eda",
           "Javier", "Marta", "David", "Elena", "Pedro", "Ana", "Pablo"]
APELLIDOS = ["Garc\u00eda", "L\u00f3pez", "Mart\u00ednez", "S\u00e1nchez", "P\u00e9rez", "G\u00f3mez", "Ruiz",
             "D\u00edaz", "Moreno", "Jim\u00e9nez", "Romero", "Navarro", "Torres", "Dom\u00ednguez", "Gil"]
CANALES = ["Google Ads", "Redes Sociales", "SEO Org\u00e1nico", "Tel\u00e9fono / Directo", "Recomendaci\u00f3n"]
P_CANALES = [0.35, 0.25, 0.20, 0.10, 0.10]
OFICINAS = {"Sevilla": "41", "Madrid": "28", "Barcelona": "08", "Valencia": "46", "M\u00e1laga": "29"}
ESTADOS = ["En Estudio", "Aceptado / En Negociaci\u00f3n", "Plan Activo", "Cancelado con \u00c9xito", "Incumplido"]
P_ESTADOS = [0.20, 0.30, 0.35, 0.10, 0.05]
ACREEDORES = ["Banco Sur", "Financiera Hispalis", "Tarjetas Mediterr\u00e1neo", "Pr\u00e9stamos R\u00e1pidos SL",
              "Caja Campi\u00f1a", "Telecom Dato", "Seguros Atl\u00e1ntico", "Consumo Ya", "Cr\u00e9dito Express",
              "Banco Norte"]
TYPOS = {"Google Ads": "Gogle Ads", "Redes Sociales": "RRSS", "Sevilla": "Sevila",
         "Barcelona": "Barna", "Valencia": "Val\u00e8ncia"}
ESTADO_EXTRA = {
    "En Estudio": ["Estudio", "en estudio"],
    "Aceptado / En Negociaci\u00f3n": ["Aceptado/En Negociacion", "Aceptado", "ACEPTADO / EN NEGOCIACI\u00d3N"],
    "Plan Activo": ["Activo", "plan  activo"],
    "Cancelado con \u00c9xito": ["Cancelado con Exito", "Cancelado"],
    "Incumplido": ["INCUMPLIDO", "Incumplido "],
}
BOOLS = ["S\u00ed", "SI", "si", "No", "NO", "no", "S", "N", "1", "0", "True", "False"]


def texto_sucio(valor, extras=None):
    if valor in TYPOS and rng.random() < 0.03:
        return TYPOS[valor]
    if extras and valor in extras and rng.random() < 0.20:
        return pick(extras[valor])
    return variante_texto(valor)


# ----------------------------------------------------------------------
# CLIENTES
# ----------------------------------------------------------------------
fecha_base = datetime(2025, 1, 1)
fechas_entrada = [fecha_base + timedelta(days=int(rng.integers(0, 300))) for _ in range(N_CLIENTES)]
oficinas_cli = [pick(list(OFICINAS)) for _ in range(N_CLIENTES)]
canales_cli = [pick(CANALES, P_CANALES) for _ in range(N_CLIENTES)]

filas = []
for i in range(1, N_CLIENTES + 1):
    nom, ap1, ap2 = pick(NOMBRES), pick(APELLIDOS), pick(APELLIDOS)
    r = rng.random()
    if r < 0.50:
        nombre = f"{nom} {ap1} {ap2}"
    elif r < 0.80:
        nombre = f"{ap1.upper()} {ap2.upper()}, {nom.upper()}"
    elif r < 0.90:
        nombre = f"{ap1} {ap2} {nom}".lower()
    else:
        nombre = f"{nom}  {ap1}"

    mail = f"{sin_tildes(nom[0]).lower()}.{sin_tildes(ap1).lower()}{int(rng.integers(1, 99))}@{pick(['example.com', 'example.org'])}"
    r = rng.random()
    if r < 0.08:
        mail = mail.upper()
    elif r < 0.11:
        mail = mail.replace("@", ".")
    elif r < 0.14:
        mail = " " + mail + " "

    dig = "".join(str(int(rng.integers(0, 10))) for _ in range(8))
    tel = pick(["6" + dig, "+34 6" + dig[:2] + " " + dig[2:5] + " " + dig[5:],
                "6" + dig[:2] + "-" + dig[2:5] + "-" + dig[5:], "0034 6" + dig,
                "(+34) 6" + dig, "6" + dig[:5]], p=[0.45, 0.20, 0.12, 0.08, 0.08, 0.07])

    ciudad = oficinas_cli[i - 1]
    prefijo_cp = OFICINAS[ciudad] if rng.random() < 0.90 else pick(list(OFICINAS.values()))
    cp = prefijo_cp + f"{int(rng.integers(0, 1000)):03d}"
    r = rng.random()
    if prefijo_cp == "08" and r < 0.35:
        cp = str(int(cp))          # se pierde el cero inicial
    elif r < 0.04:
        cp = cp[:2] + " " + cp[2:]
    elif r < 0.06:
        cp = "ABCDE"

    ingresos = "sin ingresos" if rng.random() < 0.08 else fmt_importe(round(float(rng.uniform(0, 3500)), 2))
    if rng.random() < 0.01:
        ingresos = "-" + str(int(rng.integers(100, 900)))

    filas.append({
        "ClienteId": fmt_id(i, "CLI"),
        "NombreCompleto": nombre,
        "FechaEntrada": fmt_fecha(fechas_entrada[i - 1]),
        "CanalCaptacion": texto_sucio(canales_cli[i - 1]),
        "DepartamentoOficina": texto_sucio(ciudad),
        "CodigoPostal": cp,
        "Email": mail,
        "Telefono": tel,
        "IngresosMensuales": ingresos,
        "TieneAval": pick(BOOLS),
    })

df_cli = pd.DataFrame(filas)
for col, frac in [("FechaEntrada", 0.02), ("CanalCaptacion", 0.02), ("DepartamentoOficina", 0.03),
                  ("CodigoPostal", 0.04), ("Email", 0.06), ("Telefono", 0.08),
                  ("IngresosMensuales", 0.05), ("TieneAval", 0.10)]:
    df_cli[col] = inyectar_nulos(df_cli[col], frac, "clientes_" + col)
df_cli["FechaEntrada"] = fechas_invalidas(df_cli["FechaEntrada"], 0.01, "clientes")

# duplicados exactos y casi-duplicados (mismo ClienteId, datos de contacto distintos)
dup_exactos = df_cli.sample(25, random_state=1)
casi = df_cli.sample(15, random_state=2).copy()
casi["Email"] = "nuevo." + casi["ClienteId"].astype(str).str.replace(r"\W", "", regex=True) + "@example.com"
casi["Telefono"] = "6" + casi["ClienteId"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8).str[-8:]
control["clientes_duplicados_exactos"] = 25
control["clientes_casi_duplicados"] = 15
df_cli = pd.concat([df_cli, dup_exactos, casi]).sample(frac=1, random_state=3)
df_cli = fila_basura(df_cli, "TOTAL")
df_cli.to_csv(OUT / "clientes_raw.csv", sep=";", index=False, encoding="cp1252")

# ----------------------------------------------------------------------
# EXPEDIENTES
# ----------------------------------------------------------------------
cli_con_expediente = int(N_CLIENTES * 0.85)       # el resto de clientes no tendra expediente
filas = []
huerfanos = 0
for j in range(1, N_EXPEDIENTES + 1):
    if rng.random() < 0.03:
        idx_cli = int(rng.integers(N_CLIENTES + 50, N_CLIENTES + 500))   # cliente que no existe
        f_entrada = fecha_base
        huerfanos += 1
    else:
        idx_cli = int(rng.integers(1, cli_con_expediente + 1))
        f_entrada = fechas_entrada[idx_cli - 1]

    r = rng.random()
    if r < 0.05:
        f_ap = f_entrada - timedelta(days=int(rng.integers(1, 90)))      # apertura anterior a la entrada
    elif r < 0.06:
        f_ap = datetime(2030, 1, 1)                                      # fecha futura
    else:
        f_ap = f_entrada + timedelta(days=int(rng.integers(0, 60)))

    deuda = round(float(rng.uniform(8000, 65000)), 2)
    cuota = round(float(rng.uniform(150, 700)), 2)
    deuda_txt, cuota_txt = fmt_importe(deuda), fmt_importe(cuota)
    r = rng.random()
    if r < 0.01:
        deuda_txt = pick(["0", "-1", "9999999", "-" + str(int(deuda))])
    elif r < 0.02:
        cuota_txt = pick(["a determinar", "0", "-" + str(int(cuota))])

    k = int(rng.integers(2, 9))
    acreedores = list(rng.choice(ACREEDORES, size=k, replace=False))
    acreedores = [texto_sucio(a) if rng.random() < 0.10 else a for a in acreedores]
    sep = pick(["; ", ",", " / ", " | ", " y "], p=[0.35, 0.30, 0.15, 0.10, 0.10])
    num = str(k)
    if rng.random() < 0.10:
        num = str(k + int(pick([-1, 1, 2])))                              # no coincide con la lista
    elif rng.random() < 0.06:
        num = pick(["dos", "tres", "cuatro", "cinco"])

    estado = pick(ESTADOS, P_ESTADOS)
    filas.append({
        "EXPEDIENTE-ID": fmt_id(j, "EXP"),
        "CLIENTE-ID": fmt_id(idx_cli, "CLI"),
        "FECHA-APERTURA": fmt_fecha(f_ap),
        "DEUDA-TOTAL": deuda_txt,
        "NUM-ACREEDORES": num,
        "ACREEDORES": sep.join(acreedores),
        "CUOTA-MENSUAL-PROPUESTA": cuota_txt,
        "ESTADO-EXPEDIENTE": texto_sucio(estado, ESTADO_EXTRA),
    })

control["expedientes_huerfanos_cliente_inexistente"] = huerfanos
df_exp = pd.DataFrame(filas)
for col, frac in [("CLIENTE-ID", 0.01), ("FECHA-APERTURA", 0.03), ("DEUDA-TOTAL", 0.03),
                  ("NUM-ACREEDORES", 0.04), ("ACREEDORES", 0.05),
                  ("CUOTA-MENSUAL-PROPUESTA", 0.05), ("ESTADO-EXPEDIENTE", 0.02)]:
    df_exp[col] = inyectar_nulos(df_exp[col], frac, "expedientes_" + col)
df_exp["FECHA-APERTURA"] = fechas_invalidas(df_exp["FECHA-APERTURA"], 0.01, "expedientes")

dup_exp = df_exp.sample(30, random_state=4)
casi_exp = df_exp.sample(10, random_state=5).copy()                      # mismo expediente, otro estado/deuda
casi_exp["ESTADO-EXPEDIENTE"] = pick(ESTADOS)
casi_exp["DEUDA-TOTAL"] = [fmt_importe(float(rng.uniform(8000, 65000))) for _ in range(len(casi_exp))]
control["expedientes_duplicados_exactos"] = 30
control["expedientes_casi_duplicados"] = 10
df_exp = pd.concat([df_exp, dup_exp, casi_exp]).sample(frac=1, random_state=6)
df_exp = fila_basura(df_exp, "TOTAL EXPEDIENTES")
df_exp.to_csv(OUT / "expedientes_raw.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------
# OFICINAS (tabla pequena, otro estilo de nombres de columna)
# ----------------------------------------------------------------------
df_of = pd.DataFrame({
    "nombre oficina": ["Sevilla", "Madrid", "Barcelona", "Valencia", "M\u00e1laga", "Malaga ", "SEVILLA"],
    "Responsable": ["Ana Ruiz", "Pedro Gil", "Laura Torres", "Javier D\u00edaz", "Marta Navarro", "Marta Navarro", "Carlos Gil"],
    "objetivo_conversion_%": ["35%", "0,30", "28", "0.32", "30%", "30", "0,35"],
    "Fecha Apertura": ["2019-03-01", "01/09/2018", "2020-01-15", "15-06-21", "2022/02/01", "2022/02/01", "2019-03-01"],
})
df_of.to_csv(OUT / "oficinas_raw.csv", index=False, encoding="utf-8")

# ----------------------------------------------------------------------
# Control (no abrir hasta terminar tu limpieza)
# ----------------------------------------------------------------------
(OUT / "_control.json").write_text(json.dumps(control, indent=2, ensure_ascii=False), encoding="utf-8")

print("Archivos generados en raw/:")
print(f"  clientes_raw.csv     ({len(df_cli)} filas)  -> separador ';' y codificacion cp1252")
print(f"  expedientes_raw.csv  ({len(df_exp)} filas)  -> separador ',' y codificacion utf-8")
print(f"  oficinas_raw.csv     ({len(df_of)} filas)")
print("Cuando termines tu limpieza, compara con raw/_control.json")