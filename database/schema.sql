CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    primer_apellido VARCHAR(100) NOT NULL,
    segundo_apellido VARCHAR(100),
    correo VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    foto_url TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE usuario_rol (
    usuario_id INT,
    rol_id INT,
    PRIMARY KEY (usuario_id, rol_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE carreras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE alumnos (
    id SERIAL PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL,
    numero_cuenta VARCHAR(15) UNIQUE NOT NULL,
    carrera_id INT,
    semestre INT CHECK (semestre BETWEEN 1 AND 12),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);

CREATE TABLE instructores (
    id SERIAL PRIMARY KEY,
    usuario_id INT UNIQUE NOT NULL,
    afiliacion VARCHAR(50) CHECK (afiliacion IN ('interno','externo','estudiante','profesor')),
    profesion VARCHAR(150),
    especialidad VARCHAR(150),
    biografia TEXT,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE talleres (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    detalles TEXT,

    imagen_url TEXT

    modalidad VARCHAR(20) CHECK (modalidad IN ('presencial','en_linea','hibrido')),
    ubicacion VARCHAR(200),

    fecha_inicio DATE,
    fecha_fin DATE,
    hora_inicio TIME,
    hora_fin TIME,

    numero_sesiones INT,

    cupo_total INT NOT NULL CHECK (cupo_total > 0),

    estado VARCHAR(20) DEFAULT 'pendiente'
        CHECK (estado IN ('borrador','pendiente','aprobado','concluido','cancelado')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE taller_instructor (
    taller_id INT,
    instructor_id INT,
    PRIMARY KEY (taller_id, instructor_id),

    FOREIGN KEY (taller_id) REFERENCES talleres(id) ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES instructores(id) ON DELETE CASCADE
);

CREATE TABLE temario (
    id SERIAL PRIMARY KEY,
    taller_id INT NOT NULL,
    orden INT NOT NULL,
    tema VARCHAR(300) NOT NULL,

    UNIQUE (taller_id, orden),
    FOREIGN KEY (taller_id) REFERENCES talleres(id) ON DELETE CASCADE
);

CREATE TABLE inscripciones (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    taller_id INT NOT NULL,

    estado VARCHAR(20) DEFAULT 'activa'
        CHECK (estado IN ('activa','cancelada','baja')),

    estado_final VARCHAR(20)
        CHECK (estado_final IN ('pendiente','completado','no_asistio')),

    fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_finalizacion TIMESTAMP,

    UNIQUE (usuario_id, taller_id),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (taller_id) REFERENCES talleres(id) ON DELETE CASCADE
);

CREATE TABLE certificados (
    id SERIAL PRIMARY KEY,
    inscripcion_id INT UNIQUE NOT NULL,
    codigo_verificacion VARCHAR(50) UNIQUE NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (inscripcion_id) REFERENCES inscripciones(id) ON DELETE CASCADE
);