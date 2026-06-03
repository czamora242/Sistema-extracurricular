-- ================================================================
-- SISTEMA DE GESTIÓN DE TALLERES EXTRACURRICULARES — UNAB
-- Universidad Nacional de Barranca
-- Motor: MySQL 8.0+  |  ORM: SQLAlchemy  |  Charset: utf8mb4
-- Diseñado para migración a web: estructura MVC, sin lógica en BD
-- ================================================================

CREATE DATABASE IF NOT EXISTS unab_talleres
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE unab_talleres;

-- ================================================================
-- EP-01 · AUTENTICACIÓN Y ROLES
-- ================================================================

CREATE TABLE roles (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(50)     NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Roles del sistema: Administrador, Docente, Operador';

INSERT INTO roles (nombre, descripcion) VALUES
    ('Administrador', 'Acceso total al sistema'),
    ('Docente',       'Gestiona asistencia de sus talleres asignados'),
    ('Operador',      'Gestiona bienes patrimoniales');

CREATE TABLE usuarios (
    id                INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    rol_id            INT UNSIGNED    NOT NULL,
    nombres           VARCHAR(100)    NOT NULL,
    apellidos         VARCHAR(100)    NOT NULL,
    username          VARCHAR(50)     NOT NULL UNIQUE,
    email             VARCHAR(150)    NOT NULL UNIQUE,
    password_hash     VARCHAR(255)    NOT NULL,       -- bcrypt
    activo            TINYINT(1)      NOT NULL DEFAULT 1,
    ultimo_acceso     DATETIME,
    intentos_fallidos TINYINT         NOT NULL DEFAULT 0,
    bloqueado_hasta   DATETIME,                       -- NULL = no bloqueado
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
) ENGINE=InnoDB COMMENT='Usuarios con acceso al sistema (docentes, admin, operadores)';

-- ================================================================
-- EP-02 · GESTIÓN DE ESTUDIANTES
-- ================================================================

CREATE TABLE facultades (
    id         INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    nombre     VARCHAR(150)    NOT NULL,
    codigo     VARCHAR(20)     NOT NULL UNIQUE,
    activo     TINYINT(1)      NOT NULL DEFAULT 1,
    created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE carreras (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    facultad_id INT UNSIGNED    NOT NULL,
    nombre      VARCHAR(150)    NOT NULL,
    codigo      VARCHAR(20)     NOT NULL UNIQUE,
    activo      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facultad_id) REFERENCES facultades(id)
) ENGINE=InnoDB;

CREATE TABLE estudiantes (
    id                  INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    carrera_id          INT UNSIGNED    NOT NULL,
    dni                 VARCHAR(20)     NOT NULL UNIQUE,
    codigo_estudiantil  VARCHAR(20)     NOT NULL UNIQUE,
    nombres             VARCHAR(100)    NOT NULL,
    apellidos           VARCHAR(100)    NOT NULL,
    fecha_nacimiento    DATE,
    ciclo_actual        TINYINT UNSIGNED,
    email               VARCHAR(150),
    telefono            VARCHAR(20),
    foto_ruta           VARCHAR(500),                 -- ruta relativa en disco
    estado              ENUM('Activo','Inactivo','Egresado') NOT NULL DEFAULT 'Activo',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by          INT UNSIGNED,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id),
    FOREIGN KEY (created_by) REFERENCES usuarios(id),
    INDEX idx_dni                (dni),
    INDEX idx_codigo_estudiantil (codigo_estudiantil),
    INDEX idx_estado             (estado)
) ENGINE=InnoDB COMMENT='Estudiantes inscritos en talleres extracurriculares';

-- ================================================================
-- EP-03 · GESTIÓN DE TALLERES Y SESIONES
-- ================================================================

CREATE TABLE ciclos_academicos (
    id           INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(20)     NOT NULL UNIQUE,     -- ej: "2024-I", "2025-II"
    fecha_inicio DATE            NOT NULL,
    fecha_fin    DATE            NOT NULL,
    activo       TINYINT(1)      NOT NULL DEFAULT 0,  -- solo 1 activo a la vez
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE docentes (
    id                  INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    usuario_id          INT UNSIGNED,                  -- NULL: docente sin cuenta
    dni                 VARCHAR(20)     NOT NULL UNIQUE,
    nombres             VARCHAR(100)    NOT NULL,
    apellidos           VARCHAR(100)    NOT NULL,
    especialidad        VARCHAR(150),
    email_institucional VARCHAR(150),
    telefono            VARCHAR(20),
    activo              TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB COMMENT='Docentes que dirigen talleres';

CREATE TABLE talleres (
    id                 INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    ciclo_academico_id INT UNSIGNED    NOT NULL,
    docente_id         INT UNSIGNED    NOT NULL,
    codigo             VARCHAR(20)     NOT NULL UNIQUE,   -- generado automáticamente
    nombre             VARCHAR(200)    NOT NULL,
    descripcion        TEXT,
    categoria          VARCHAR(100),
    sede               VARCHAR(200),
    cupo_maximo        SMALLINT UNSIGNED NOT NULL DEFAULT 30,
    horas_totales      SMALLINT UNSIGNED,
    umbral_asistencia  TINYINT UNSIGNED  NOT NULL DEFAULT 80,  -- 50–100
    estado             ENUM('Activo','Suspendido','Finalizado','EnRiesgo') NOT NULL DEFAULT 'Activo',
    created_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by         INT UNSIGNED,
    FOREIGN KEY (ciclo_academico_id) REFERENCES ciclos_academicos(id),
    FOREIGN KEY (docente_id)         REFERENCES docentes(id),
    FOREIGN KEY (created_by)         REFERENCES usuarios(id),
    INDEX idx_estado (estado),
    INDEX idx_ciclo  (ciclo_academico_id)
) ENGINE=InnoDB COMMENT='Talleres extracurriculares por ciclo académico';

CREATE TABLE sesiones (
    id             INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    taller_id      INT UNSIGNED    NOT NULL,
    numero_sesion  TINYINT UNSIGNED NOT NULL,
    fecha          DATE            NOT NULL,
    hora_inicio    TIME            NOT NULL,
    hora_fin       TIME            NOT NULL,
    estado         ENUM('Programada','Realizada','Cancelada') NOT NULL DEFAULT 'Programada',
    observaciones  TEXT,
    created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (taller_id) REFERENCES talleres(id),
    UNIQUE KEY uq_taller_sesion (taller_id, numero_sesion),
    INDEX idx_fecha (fecha)
) ENGINE=InnoDB COMMENT='Sesiones individuales de cada taller';

-- ================================================================
-- EP-02 + EP-03 · INSCRIPCIONES (tabla pivot)
-- ================================================================

CREATE TABLE inscripciones (
    id                INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    taller_id         INT UNSIGNED    NOT NULL,
    estudiante_id     INT UNSIGNED    NOT NULL,
    fecha_inscripcion DATE            NOT NULL DEFAULT (CURRENT_DATE),
    estado            ENUM('Activo','Retirado') NOT NULL DEFAULT 'Activo',
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        INT UNSIGNED,
    FOREIGN KEY (taller_id)     REFERENCES talleres(id),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    FOREIGN KEY (created_by)    REFERENCES usuarios(id),
    UNIQUE KEY uq_taller_estudiante (taller_id, estudiante_id)  -- sin duplicados
) ENGINE=InnoDB COMMENT='Un estudiante inscrito en un taller';

-- ================================================================
-- EP-04 · REGISTRO DE ASISTENCIA
-- ================================================================

CREATE TABLE asistencia (
    id              INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    inscripcion_id  INT UNSIGNED    NOT NULL,
    sesion_id       INT UNSIGNED    NOT NULL,
    estado          ENUM('P','A','J') NOT NULL DEFAULT 'A',  -- Presente/Ausente/Justificado
    observacion     TEXT,                                    -- requerido si estado=J
    registrado_por  INT UNSIGNED,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (inscripcion_id) REFERENCES inscripciones(id),
    FOREIGN KEY (sesion_id)      REFERENCES sesiones(id),
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id),
    UNIQUE KEY uq_inscripcion_sesion (inscripcion_id, sesion_id)  -- 1 registro por alumno/sesión
) ENGINE=InnoDB COMMENT='Asistencia P/A/J por estudiante por sesión';

-- ================================================================
-- EP-05 · LISTA DE APTOS
-- El sistema genera una lista Excel de alumnos que superaron el
-- umbral de asistencia. NO emite certificados individuales.
-- El certificado oficial lo gestiona la Dirección de Servicios
-- Académicos de forma independiente con esta lista como insumo.
-- ================================================================

CREATE TABLE listas_aptos (
    id              INT UNSIGNED      AUTO_INCREMENT PRIMARY KEY,
    taller_id       INT UNSIGNED      NOT NULL,
    ciclo_academico_id INT UNSIGNED   NOT NULL,
    fecha_emision   DATE              NOT NULL DEFAULT (CURRENT_DATE),
    total_inscritos SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    total_aptos     SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    umbral_aplicado TINYINT UNSIGNED  NOT NULL,            -- snapshot del umbral al momento de generar
    generado_por    INT UNSIGNED,
    ruta_excel      VARCHAR(500),                          -- ruta relativa del .xlsx generado
    observaciones   TEXT,
    created_at      DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (taller_id)          REFERENCES talleres(id),
    FOREIGN KEY (ciclo_academico_id) REFERENCES ciclos_academicos(id),
    FOREIGN KEY (generado_por)       REFERENCES usuarios(id),
    INDEX idx_taller (taller_id),
    INDEX idx_fecha  (fecha_emision)
) ENGINE=InnoDB COMMENT='Registro de cada emisión de lista de alumnos aptos por taller';

CREATE TABLE lista_aptos_detalle (
    id                    INT UNSIGNED      AUTO_INCREMENT PRIMARY KEY,
    lista_id              INT UNSIGNED      NOT NULL,
    estudiante_id         INT UNSIGNED      NOT NULL,
    codigo_estudiantil    VARCHAR(20)       NOT NULL,      -- snapshot al momento de generar
    nombres               VARCHAR(200)      NOT NULL,      -- snapshot: evita depender de JOIN
    carrera               VARCHAR(150)      NOT NULL,      -- snapshot
    sesiones_asistidas    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    sesiones_totales      SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    porcentaje_asistencia DECIMAL(5,2)      NOT NULL,
    es_apto               TINYINT(1)        NOT NULL DEFAULT 0,
    excluido_manual       TINYINT(1)        NOT NULL DEFAULT 0,  -- coordinador puede excluir antes de confirmar
    motivo_exclusion      VARCHAR(300),
    FOREIGN KEY (lista_id)      REFERENCES listas_aptos(id),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id),
    UNIQUE KEY uq_lista_estudiante (lista_id, estudiante_id)
) ENGINE=InnoDB COMMENT='Detalle por alumno: apto, porcentaje y datos al momento de la emisión';

-- ================================================================
-- EP-06 · GESTIÓN DE BIENES PATRIMONIALES
-- ================================================================

CREATE TABLE bienes_patrimoniales (
    id                 INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    codigo_patrimonial VARCHAR(50)     NOT NULL UNIQUE,
    descripcion        VARCHAR(300)    NOT NULL,
    categoria          VARCHAR(100),
    valor_adquisicion  DECIMAL(10,2),
    fecha_adquisicion  DATE,
    estado             ENUM('Disponible','Asignado','Mantenimiento','DeBaja') NOT NULL DEFAULT 'Disponible',
    observaciones      TEXT,
    created_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Inventario de bienes patrimoniales';

CREATE TABLE asignaciones_bien (
    id                        INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    bien_id                   INT UNSIGNED    NOT NULL,
    docente_id                INT UNSIGNED,            -- a quién se le asigna
    taller_id                 INT UNSIGNED,            -- en qué taller se usa
    fecha_asignacion          DATE            NOT NULL,
    fecha_devolucion_esperada DATE,
    fecha_devolucion_real     DATE,
    estado_conservacion       ENUM('Excelente','Bueno','Regular','Malo','Inservible'),
    observaciones_asignacion  TEXT,
    observaciones_devolucion  TEXT,
    recibido_por_nombre       VARCHAR(200),            -- firma de recepción
    estado_asignacion         ENUM('Activo','Devuelto') NOT NULL DEFAULT 'Activo',
    asignado_por              INT UNSIGNED,
    created_at                DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bien_id)      REFERENCES bienes_patrimoniales(id),
    FOREIGN KEY (docente_id)   REFERENCES docentes(id),
    FOREIGN KEY (taller_id)    REFERENCES talleres(id),
    FOREIGN KEY (asignado_por) REFERENCES usuarios(id)
) ENGINE=InnoDB COMMENT='Asignación y devolución de bienes (Formato N°03)';

-- ================================================================
-- EP-01 · AUDITORÍA CENTRALIZADA
-- ================================================================

CREATE TABLE auditoria (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id       INT UNSIGNED,
    tabla_afectada   VARCHAR(100)    NOT NULL,
    accion           ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    registro_id      INT UNSIGNED,
    datos_anteriores JSON,                                    -- snapshot antes
    datos_nuevos     JSON,                                    -- snapshot después
    ip_address       VARCHAR(45),                            -- IPv4 e IPv6
    created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    INDEX idx_tabla   (tabla_afectada),
    INDEX idx_created (created_at),
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB COMMENT='Trazabilidad completa de cambios en el sistema';

-- ================================================================
-- VISTAS DE NEGOCIO (reutilizables desde Python/SQLAlchemy)
-- ================================================================

-- Vista: porcentaje de asistencia acumulado por inscripción
CREATE OR REPLACE VIEW v_asistencia_resumen AS
SELECT
    i.id          AS inscripcion_id,
    i.taller_id,
    i.estudiante_id,
    COUNT(a.id)   AS sesiones_registradas,
    SUM(CASE WHEN a.estado IN ('P','J') THEN 1 ELSE 0 END)  AS sesiones_validas,
    (SELECT COUNT(*) FROM sesiones s
     WHERE s.taller_id = i.taller_id AND s.estado = 'Realizada') AS sesiones_realizadas,
    ROUND(
        SUM(CASE WHEN a.estado IN ('P','J') THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(
            (SELECT COUNT(*) FROM sesiones s
             WHERE s.taller_id = i.taller_id AND s.estado = 'Realizada'), 0)
    , 2)           AS porcentaje_asistencia
FROM inscripciones i
LEFT JOIN asistencia a ON a.inscripcion_id = i.id
WHERE i.estado = 'Activo'
GROUP BY i.id, i.taller_id, i.estudiante_id;

-- Vista: estudiantes aptos/no-aptos por taller (en tiempo real, antes de emitir lista)
-- Uso: previsualización antes de generar la lista oficial
CREATE OR REPLACE VIEW v_estudiantes_aptos AS
SELECT
    t.id                    AS taller_id,
    t.nombre                AS taller_nombre,
    t.umbral_asistencia,
    ca.nombre               AS ciclo,
    e.id                    AS estudiante_id,
    CONCAT(e.nombres, ' ', e.apellidos) AS estudiante_nombre,
    e.codigo_estudiantil,
    c.nombre                AS carrera,
    v.sesiones_validas,
    v.sesiones_realizadas,
    v.porcentaje_asistencia,
    (v.porcentaje_asistencia >= t.umbral_asistencia) AS es_apto
FROM talleres t
JOIN ciclos_academicos ca   ON ca.id = t.ciclo_academico_id
JOIN inscripciones i        ON i.taller_id = t.id AND i.estado = 'Activo'
JOIN estudiantes e          ON e.id = i.estudiante_id
JOIN carreras c             ON c.id = e.carrera_id
JOIN v_asistencia_resumen v ON v.inscripcion_id = i.id;

-- Vista: estado de bienes con su última asignación
CREATE OR REPLACE VIEW v_bienes_estado AS
SELECT
    bp.id,
    bp.codigo_patrimonial,
    bp.descripcion,
    bp.categoria,
    bp.estado,
    ab.estado_asignacion,
    CONCAT(d.nombres, ' ', d.apellidos) AS docente_asignado,
    t.nombre                             AS taller_asignado,
    ab.fecha_asignacion,
    ab.fecha_devolucion_esperada
FROM bienes_patrimoniales bp
LEFT JOIN asignaciones_bien ab ON ab.bien_id = bp.id AND ab.estado_asignacion = 'Activo'
LEFT JOIN docentes d            ON d.id = ab.docente_id
LEFT JOIN talleres t            ON t.id = ab.taller_id;
