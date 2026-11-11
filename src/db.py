# =======================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS Y ESQUEMAS
# =======================================================================

NOMBRE_BD = "deuda_analytics"


# TABLA MAESTRA: OFICINAS
# -----------------------------------------------------------------------
TABLA_OFICINAS = "oficinas"
ESQUEMA_OFICINAS = '''
    oficina_id INT PRIMARY KEY,
    nombre_oficina VARCHAR(50) NOT NULL,
    responsable VARCHAR(100),
    objetivo_conversion_pct DECIMAL(4,1),
    fecha_apertura_oficina DATE
'''

# TABLA MAESTRA: CANALES DE CAPTACIÓN
# -----------------------------------------------------------------------
TABLA_CANALES = "canales"
ESQUEMA_CANALES = '''
    canal_id INT PRIMARY KEY,
    canal_nombre VARCHAR(50) NOT NULL
'''

# TABLA MAESTRA: ESTADOS DEL EXPEDIENTE
# -----------------------------------------------------------------------
TABLA_ESTADOS = "estados"
ESQUEMA_ESTADOS = '''
    estado_id INT PRIMARY KEY,
    estado_nombre VARCHAR(50) NOT NULL
'''

# TABLA PADRE: CLIENTES
# -----------------------------------------------------------------------
TABLA_CLIENTES = "clientes"
ESQUEMA_CLIENTES = '''
    cliente_id INT PRIMARY KEY,
    nombre_completo VARCHAR(150),
    fecha_entrada DATE,
    canal_id INT,
    oficina_id INT,
    codigo_postal VARCHAR(5),
    email VARCHAR(150),
    telefono VARCHAR(9),
    ingresos_mensuales DECIMAL(10,2),
    tiene_aval BOOLEAN,
    FOREIGN KEY (canal_id) REFERENCES canales(canal_id),
    FOREIGN KEY (oficina_id) REFERENCES oficinas(oficina_id)
'''

# TABLA HIJA: EXPEDIENTES (un cliente puede tener 0 o varios expedientes)
# -----------------------------------------------------------------------
TABLA_EXPEDIENTES = "expedientes"
ESQUEMA_EXPEDIENTES = '''
    expediente_id INT PRIMARY KEY,
    cliente_id INT,
    fecha_apertura DATE,
    deuda_total DECIMAL(12,2),
    num_acreedores INT,
    acreedores TEXT,
    cuota_mensual_propuesta DECIMAL(10,2),
    estado_id INT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id) ON DELETE CASCADE,
    FOREIGN KEY (estado_id) REFERENCES estados(estado_id)
'''
