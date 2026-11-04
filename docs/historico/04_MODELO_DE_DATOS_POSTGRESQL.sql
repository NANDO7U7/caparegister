-- DISEÑO HISTÓRICO: solo referencia de planificación.
-- No sustituye las migraciones Django de sigecap/apps/*/migrations/.
-- No ejecutar para inicializar o actualizar la base de datos de la aplicación.
-- ============================================================================
-- SISTEMA DE GESTIÓN DE CAPACITACIONES DOCENTES Y ADMINISTRATIVAS (SGCDA)
-- Script de Creación del Modelo de Datos Relacional para PostgreSQL (v14+)
-- Blindado contra vulnerabilidades e integrado con Django ORM
-- ============================================================================

-- Habilitar extensión para identificadores universales únicos (UUID)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CATÁLOGOS BASE DEL SISTEMA (Gestionables desde Django Admin)
-- ============================================================================

-- 1.1 Facultades o Unidades Organizacionales
CREATE TABLE facultades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 Áreas de Formación (Ejes Formativos)
CREATE TABLE areas_formacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 Tipos y Modalidades de Capacitación
CREATE TABLE tipos_modalidad (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo VARCHAR(50) NOT NULL, -- Taller, Curso, Diplomado, Congreso, Conferencia
    modalidad VARCHAR(30) NOT NULL, -- Presencial, Virtual, Híbrida
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tipo_modalidad UNIQUE (tipo, modalidad)
);

-- 1.4 Proyectos o Fuentes de Financiamiento
CREATE TABLE proyectos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    fuente_financiamiento VARCHAR(100), -- Fondos Propios, Cooperación Externa, Convenio
    presupuesto_asignado NUMERIC(14, 2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 1.5 Proveedores e Instituciones Capacitadoras
CREATE TABLE proveedores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(30) UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Interno', 'Externo')),
    pais VARCHAR(80) DEFAULT 'Local',
    contacto_nombre VARCHAR(150),
    contacto_email VARCHAR(150),
    contacto_telefono VARCHAR(50),
    observaciones TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. PERSONAS, USUARIOS Y CONTROL DE ACCESO SEGURO
-- ============================================================================

-- 2.1 Padrón General de Personas (Docentes y Administrativos)
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_empleado VARCHAR(50) UNIQUE NOT NULL,
    documento_identidad VARCHAR(50) UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    tipo_personal VARCHAR(20) NOT NULL CHECK (tipo_personal IN ('Docente', 'Administrativo', 'Ambos')),
    facultad_id UUID REFERENCES facultades(id) ON DELETE RESTRICT,
    departamento_unidad VARCHAR(150),
    cargo_actual VARCHAR(150),
    email_institucional VARCHAR(150) UNIQUE,
    telefono VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 Cuentas de Acceso al Sistema con Control Anti-Fuerza Bruta
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID UNIQUE REFERENCES personas(id) ON DELETE SET NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Hashed con PBKDF2 / Argon2 + Salt
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('ADMINISTRADOR', 'GESTOR', 'DIRECTIVO', 'DOCENTE')),
    activo BOOLEAN DEFAULT TRUE,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP WITH TIME ZONE,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. CAPACITACIONES Y EVENTOS FORMATIVOS
-- ============================================================================

-- 3.1 Eventos de Capacitación
CREATE TABLE capacitaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(250) NOT NULL,
    descripcion TEXT,
    area_formacion_id UUID NOT NULL REFERENCES areas_formacion(id) ON DELETE RESTRICT,
    tipo_modalidad_id UUID NOT NULL REFERENCES tipos_modalidad(id) ON DELETE RESTRICT,
    horas_duracion INTEGER NOT NULL CHECK (horas_duracion > 0),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Planificada' CHECK (estado IN ('Planificada', 'En Curso', 'Finalizada', 'Cancelada')),
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE SET NULL,
    proyecto_id UUID REFERENCES proyectos(id) ON DELETE SET NULL,
    anio_periodo INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM fecha_inicio)::INTEGER) STORED,
    observaciones TEXT,
    created_by UUID REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fechas CHECK (fecha_fin >= fecha_inicio)
);

-- 3.2 Relación Muchos a Muchos: Capacitaciones con Facultades Beneficiadas
CREATE TABLE capacitacion_facultades (
    capacitacion_id UUID NOT NULL REFERENCES capacitaciones(id) ON DELETE CASCADE,
    facultad_id UUID NOT NULL REFERENCES facultades(id) ON DELETE CASCADE,
    PRIMARY KEY (capacitacion_id, facultad_id)
);

-- ============================================================================
-- 4. PARTICIPACIONES Y REGISTRO DE ASISTENCIA / APROBACIÓN
-- ============================================================================

CREATE TABLE participaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capacitacion_id UUID NOT NULL REFERENCES capacitaciones(id) ON DELETE CASCADE,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE RESTRICT,
    estado_participacion VARCHAR(20) NOT NULL DEFAULT 'Inscrito' CHECK (estado_participacion IN ('Inscrito', 'Asistió', 'Aprobó', 'No Completó')),
    calificacion_final NUMERIC(5, 2),
    horas_reconocidas INTEGER,
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_participacion UNIQUE (capacitacion_id, persona_id)
);

-- ============================================================================
-- 5. PRESUPUESTO Y COSTOS ASOCIADOS
-- ============================================================================

CREATE TABLE costos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capacitacion_id UUID NOT NULL REFERENCES capacitaciones(id) ON DELETE CASCADE,
    concepto VARCHAR(150) NOT NULL, -- Inscripción, Transporte, Viáticos, Materiales, Alquiler
    tipo_rubro VARCHAR(50) DEFAULT 'General',
    monto_presupuestado NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    monto_ejecutado NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    proyecto_id UUID REFERENCES proyectos(id) ON DELETE SET NULL,
    moneda VARCHAR(5) DEFAULT 'USD',
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. EVIDENCIAS DIGITALES BLINDADAS (DIPLOMAS, CONSTANCIAS, ASISTENCIAS)
-- ============================================================================

CREATE TABLE evidencias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capacitacion_id UUID NOT NULL REFERENCES capacitaciones(id) ON DELETE CASCADE,
    participacion_id UUID REFERENCES participaciones(id) ON DELETE CASCADE, -- Opcional, si es diploma individual
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,              -- Opcional, si corresponde a una persona
    tipo_documento VARCHAR(50) NOT NULL CHECK (tipo_documento IN ('Diploma Individual', 'Constancia', 'Lista de Asistencia', 'Programa', 'Informe Final', 'Otro')),
    nombre_archivo_original VARCHAR(255) NOT NULL,
    nombre_almacenado_uuid VARCHAR(100) NOT NULL UNIQUE, -- Almacenado como UUIDv4 sin nombres ejecutables
    ruta_almacenamiento VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL CHECK (mime_type IN ('application/pdf', 'image/png', 'image/jpeg')),
    tamano_bytes BIGINT NOT NULL CHECK (tamano_bytes <= 10485760), -- Límite estricto de 10 MB
    hash_sha256 VARCHAR(64) NOT NULL, -- Hash de integridad contra alteraciones
    metadatos_adicionales JSONB, -- Folio, número de registro o notas institucionales
    subido_por UUID REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 7. AUDITORÍA INMUTABLE (APPEND-ONLY)
-- ============================================================================

CREATE TABLE auditoria_log (
    id BIGSERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(50) NOT NULL, -- INSERT, UPDATE, DELETE, LOGIN, LOGIN_FAILED, EXPORT
    tabla_afectada VARCHAR(50) NOT NULL,
    registro_id UUID,
    datos_previos JSONB,
    datos_nuevos JSONB,
    direccion_ip VARCHAR(45) NOT NULL,
    user_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- TRIGGER DE SEGURIDAD: Prohibir estrictamente UPDATE y DELETE en la bitácora de auditoría
CREATE OR REPLACE FUNCTION bloquear_modificacion_auditoria()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Operación denegada por seguridad: La bitácora de auditoría es estrictamente inmutable (Append-Only).';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_proteger_auditoria
BEFORE UPDATE OR DELETE ON auditoria_log
FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_auditoria();

-- ============================================================================
-- 8. ÍNDICES DE RENDIMIENTO PARA REPORTES Y DASHBOARDS
-- ============================================================================

CREATE INDEX idx_capacitaciones_anio ON capacitaciones (anio_periodo);
CREATE INDEX idx_capacitaciones_estado ON capacitaciones (estado);
CREATE INDEX idx_capacitaciones_area ON capacitaciones (area_formacion_id);
CREATE INDEX idx_personas_codigo ON personas (codigo_empleado);
CREATE INDEX idx_personas_facultad ON personas (facultad_id);
CREATE INDEX idx_participaciones_persona ON participaciones (persona_id);
CREATE INDEX idx_participaciones_capacitacion ON participaciones (capacitacion_id);
CREATE INDEX idx_costos_capacitacion ON costos (capacitacion_id);
CREATE INDEX idx_evidencias_participacion ON evidencias (participacion_id);
CREATE INDEX idx_auditoria_usuario ON auditoria_log (usuario_id, created_at);

-- ============================================================================
-- 9. DATOS SEMILLA INICIALES (SEED DATA)
-- ============================================================================

-- Áreas de Formación solicitadas
INSERT INTO areas_formacion (codigo, nombre, descripcion) VALUES
('AF-INST', 'Área Institucional', 'Talleres, inducción y capacitaciones de interés general universitario'),
('AF-PEDAG', 'Formación Pedagógica', 'Didáctica universitaria, metodologías activas y evaluación de aprendizajes'),
('AF-ESPEC', 'Formación de Especialidad', 'Actualización disciplinar técnica y profesional por carrera o facultad'),
('AF-INTEG', 'Formación Integral', 'Idiomas (Inglés), Lengua de Señas, habilidades blandas y liderazgo');

-- Tipos y Modalidades Base
INSERT INTO tipos_modalidad (tipo, modalidad, descripcion) VALUES
('Taller', 'Presencial', 'Actividad práctica intensiva'),
('Taller', 'Virtual', 'Taller sincrónico en plataforma virtual'),
('Taller', 'Híbrida', 'Sesiones presenciales y remotas'),
('Curso', 'Presencial', 'Curso formativo regular'),
('Curso', 'Virtual', 'Curso en línea'),
('Curso', 'Híbrida', 'Curso semipresencial'),
('Diplomado', 'Virtual', 'Programa modular de especialización virtual'),
('Diplomado', 'Presencial', 'Programa modular presencial'),
('Congreso', 'Presencial', 'Participación en ponencias y conferencias'),
('Congreso', 'Virtual', 'Congreso en línea');

-- Facultades de Ejemplo
INSERT INTO facultades (codigo, nombre, descripcion) VALUES
('FAC-ING', 'Facultad de Ingeniería y Arquitectura', 'Carreras de ingeniería, sistemas y arquitectura'),
('FAC-MED', 'Facultad de Ciencias de la Salud', 'Medicina, enfermería y odontología'),
('FAC-ECO', 'Facultad de Ciencias Económicas', 'Administración, economía y contaduría'),
('FAC-JUR', 'Facultad de Jurisprudencia y Ciencias Sociales', 'Derecho, relaciones internacionales y trabajo social'),
('DIR-ADMIN', 'Dirección de Administración y Finanzas', 'Personal administrativo central');

-- Proyecto / Fondo base
INSERT INTO proyectos (codigo, nombre, fuente_financiamiento, presupuesto_asignado) VALUES
('FONDOS-UNIV', 'Presupuesto Operativo Ordinario de Capacitación', 'Fondos Propios', 50000.00),
('COOP-EXT', 'Fondo de Fortalecimiento a la Docencia', 'Cooperación Externa', 25000.00);

-- Proveedor institucional interno inicial
INSERT INTO proveedores (codigo, nombre, tipo, pais, observaciones) VALUES
('PROV-INTERNO', 'Unidad de Formación y Desarrollo Docente Universitario', 'Interno', 'Local', 'Capacitadores internos de la universidad');
