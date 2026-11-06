# Pipeline Deudas 💶

Proyecto individual de limpieza y transformación de datos (EDA y ETL) sobre un dataset ficticio de una empresa de gestión de deudas, con tres tablas: clientes, expedientes y oficinas. Los datos crudos tienen problemas de calidad típicos (formatos mezclados, duplicados, nulos escritos como texto, filas basura) y el objetivo es dejarlos limpios y coherentes entre sí para cargarlos después en una base de datos relacional y analizarlos con SQL.

Todos los datos son ficticios. No hay información real de personas.

## Tech Stack 🔧

Python · Jupyter Notebook · pandas · numpy

Librerías usadas:

- `pandas`: lectura, limpieza y transformación de los datos
- `numpy`: manejo de valores nulos
- `pathlib`: rutas de entrada y salida de los archivos

## Project Structure 🧬

```
raw/
├── clientes_raw.csv           — Datos crudos de clientes
├── expedientes_raw.csv        — Datos crudos de expedientes
└── oficinas_raw.csv           — Datos crudos de oficinas

clean/
├── clientes_clean.csv         — Clientes limpios
├── expedientes_clean.csv      — Expedientes limpios
└── oficinas_clean.csv         — Oficinas limpias

jupyter/
└── EDA.ipynb                  — Exploración y limpieza completa de las tres tablas

generar_datos_sucios.py        — Script que genera los datos ficticios con errores
README.md
```

## Project Overview 🔩

**Fase 1 — Datos crudos** (`generar_datos_sucios.py`, `raw/`)

- Tres tablas ficticias: clientes (843 filas), expedientes (1043 filas) y oficinas (7 filas).
- Todas las columnas llegan como texto.
- `clientes_raw.csv` se lee con separador `;` y codificación `cp1252`.

**Fase 2 — Exploración (EDA)** (`jupyter/EDA.ipynb`)

Revisión de tipos, nulos, duplicados y muestras de cada tabla. Problemas detectados:

- Mayúsculas y minúsculas mezcladas, espacios dobles y erratas (`Barna`, `Sevila`, `Gogle Ads`).
- Identificadores con prefijos distintos (`CLI_0572`, `CLI0023`, `cli-625`, `EXP_965`, `EXP0808`).
- Fechas en formatos mezclados (`2025-08-31`, `24/03/2025`, `05.05.2025`, `12-09-25`, `July 30, 2025`) y fechas imposibles (`31/02/2025`, `00/00/0000`).
- Importes con símbolo, texto y separadores distintos (`€ 2794`, `1815 EUR`, `3.209,17`, `1497.82`).
- Teléfonos con prefijos `+34` o `0034`, guiones, paréntesis y números incompletos.
- Códigos postales sin el cero inicial.
- Valores de sí/no en muchas variantes (`True`, `SI`, `Sí`, `S`, `1`, `no`, `N`, `0`...).
- Nulos escritos como `n/d`, `N/D`, `-` o `Sin ingresos`.
- Filas basura: cabecera repetida, fila de total (`840 registros`) y filas vacías.
- Filas duplicadas (25 exactas en clientes y 30 en expedientes) y `ClienteId` repetidos con distinto email.
- Ingresos negativos (10 casos).

**Fase 3 — Limpieza** (`jupyter/EDA.ipynb`)

Una función por columna, cada una con su propia regex y sus condiciones.

*Clientes*

- `ClienteId`: se quita el prefijo y se pasa a entero. Se eliminan la cabecera repetida, la fila de total y las filas vacías.
- Texto (`NombreCompleto`, `CanalCaptacion`, `DepartamentoOficina`): espacios unificados y formato título.
- `Email`: se pasa a minúsculas y se valida que tenga una estructura correcta. Si no, queda como nulo.
- `Telefono`: se quedan los 9 últimos dígitos y debe empezar por 6 o 7. Si no, queda como nulo. Se mantiene como texto.
- `CodigoPostal`: 5 dígitos, rellenando con ceros por la izquierda. Se mantiene como texto.
- `IngresosMensuales`: se quitan símbolos y texto, y se distinguen los separadores de miles y de decimales. Los negativos pasan a valor absoluto.
- `TieneAval`: pasa a booleano. Lo que no es sí o no queda como nulo.
- `FechaEntrada`: formatos unificados en fecha, con el día primero. Las fechas inválidas quedan como nulo.
- `DepartamentoOficina` y `CanalCaptacion`: diccionario de correcciones para erratas, tildes y abreviaturas.

*Expedientes*

- Nombres de columnas renombrados al mismo estilo que clientes (`EXPEDIENTE-ID` pasa a `ExpedienteId`).
- `ExpedienteId` y `ClienteId`: sin prefijo y en entero. `ClienteId` admite nulos, y solo se eliminan las filas sin `ExpedienteId` válido.
- `FechaApertura`, `DeudaTotal` y `CuotaMensualPropuesta`: las mismas reglas de fechas e importes que en clientes.
- `NumAcreedores`: entero con nulos.
- `Acreedores`: separador unificado en `; ` (había `;`, `,`, `/`, `|` y la palabra "y").
- `EstadoExpediente`: se reducen las variantes a cinco estados (Plan Activo, Aceptado / En Negociación, En Estudio, Cancelado Con Éxito, Incumplido) más nulos.

*Oficinas*

- Columnas renombradas a `NombreOficina`, `Responsable`, `ObjetivoConversionPct` y `FechaAperturaOficina`.
- `ObjetivoConversionPct`: todo en porcentaje (`35%`, `0,30` y `28` pasan a 35.0, 30.0 y 28.0).
- `NombreOficina`: formato título y `Malaga` corregido a `Málaga`.
- Fechas con las mismas reglas que en el resto de tablas.

**Fase 4 — Comprobaciones y exportación**

- Comparación de `NumAcreedores` con los acreedores que aparecen en la lista.
- Expedientes cuyo `ClienteId` no existe en la tabla de clientes.
- Comprobación de `ClienteId` y `ExpedienteId` repetidos.
- Porcentaje de nulos por columna.
- Exportación de las tres tablas a `clean/` con separador `;` y codificación UTF-8.

## Decisiones y supuestos 📝

Algunas decisiones no se pueden comprobar con los datos y son supuestos:

- **Ingresos negativos:** se pasan a valor absoluto, asumiendo error de signo.
- **Fechas:** se interpretan con el día primero (`09/02/2025` es 9 de febrero) y los años de dos cifras como 20xx.
- **Nulos:** `n/d`, `N/D`, `-` y `Sin ingresos` se tratan como nulos. Un nulo en `TieneAval` no se convierte en `False`.
- **ClienteId repetidos con distinto email:** se conserva la fila que no tiene el email de relleno (`nuevo.xxx@...`).
- **Estados de expediente:** `Activo`, `Estudio`, `Cancelado` y `Aceptado` se tratan como versiones recortadas del estado completo.
- **Canal de captación:** `Rrss` se interpreta como Redes Sociales.
- **Oficinas:** `Málaga` aparecía duplicada (idéntica) y se elimina. `Sevilla` aparece con dos responsables distintos y se conserva la primera fila.
- **Expedientes sin cliente:** se mantienen, con `ClienteId` nulo, y quedan documentados.

## Relaciones entre tablas

- `expedientes.ClienteId` → `clientes.ClienteId`
- `clientes.DepartamentoOficina` → `oficinas.NombreOficina`

## Getting Started ▶️

Clonar el repositorio:

```
git clone https://github.com/MATC-90/Pipeline_deudas.git
```

Instalar las librerías:

```
pip install pandas numpy jupyter
```

Generar los datos crudos:

```
python generar_datos_sucios.py
```

Ejecutar el notebook:

Abrir `jupyter/EDA.ipynb` y ejecutarlo de arriba abajo. Lee los datos de `raw/` y genera los tres CSV limpios en `clean/`. Las rutas son relativas, así que el notebook debe abrirse desde la carpeta `jupyter/`.

## Próximos pasos 🚧

- Crear las tablas en PostgreSQL y cargar los CSV limpios.
- Escribir consultas SQL sobre los datos (joins, agregaciones y funciones de ventana).
- Decidir cómo resolver los casos pendientes (oficina de Sevilla, expedientes sin cliente).