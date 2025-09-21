-- ===============================
-- Proyecto Maestro(s) — init_db.sql
-- ===============================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;

-- ===============================
-- Tabla: autores
-- ===============================
CREATE TABLE IF NOT EXISTS autores (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);

-- ===============================
-- Tabla: obras
-- ===============================
CREATE TABLE IF NOT EXISTS obras (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    autor_id INT REFERENCES autores(id) ON DELETE SET NULL,
    anio INT,
    tipo TEXT,
    comuna TEXT,
    barrio TEXT,
    direccion TEXT,
    descripcion TEXT,
    ubicacion GEOGRAPHY(POINT, 4326), -- lat/long
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- Tabla: rutas
-- ===============================
CREATE TABLE IF NOT EXISTS rutas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    obras_ids INT[] DEFAULT '{}', -- lista de obras incluidas
    distancia_total NUMERIC, -- km
    duracion_estimada NUMERIC, -- minutos
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_obras_autor_id ON obras(autor_id);
CREATE INDEX IF NOT EXISTS idx_obras_comuna ON obras(comuna);
CREATE INDEX IF NOT EXISTS idx_obras_tipo ON obras(tipo);
CREATE INDEX IF NOT EXISTS idx_obras_ubicacion ON obras USING GIST (ubicacion);
