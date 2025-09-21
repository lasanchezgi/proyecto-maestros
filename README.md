# Proyecto Maestro(s)

## 1. Introducción

Proyecto Maestro(s) es una aplicación web para explorar las obras públicas y sus autores en Medellín. Integra catálogos navegables y un mapa interactivo basado en datos abiertos.

**Objetivo del MVP:** permitir explorar obras y autores mediante filtros, paginación y visualización geográfica.

## 2. Estructura del Proyecto

``` bash
app/
 ├─ repositories/   # Acceso a la base de datos (SQL, PostGIS)
 ├─ services/       # Lógica de negocio y validación de filtros
 ├─ web/
 │   ├─ routes/     # Blueprints Flask
 │   ├─ templates/  # HTML con Jinja2
 │   ├─ static/     # CSS, JS y assets
 └─ utils/          # Utilidades como conexión a DB
scripts/            # Scripts auxiliares (ej. carga inicial de datos)
tests/              # Pruebas con pytest
```

## 3. Funcionalidades del MVP

- **Landing Page** con enlaces rápidos a Catálogo de Obras, Catálogo de Autores y Mapa interactivo.
- **Catálogo de Obras** con filtros por autor, comuna, tipo, año, paginación y filtro geográfico (`lat`, `lon`, `radius`).
- **Catálogo de Autores** con filtros por nombre, rango de cantidad de obras (min/max) y paginación.
- **Mapa Interactivo** con Leaflet.js, mostrando las obras georreferenciadas y popups descriptivos.
- **API interna** `/api/obras_geo` que retorna obras con coordenadas (`id`, `nombre`, `autor`, `anio`, `tipo`, `comuna`, `lat`, `lon`).

### Datos incluidos

El proyecto incluye **156 esculturas públicas** de Medellín con información de **67 autores** diferentes. Los datos provienen del archivo `data/esculturas-publicas-medellin-limpio.csv` y incluyen:

- Información básica: nombre, autor, año, tipo, comuna/área, dirección
- Coordenadas geográficas para 9 obras emblemáticas
- Datos geoespaciales almacenados en formato PostGIS

## 4. Instalación y Configuración

1. Clonar el repositorio.
2. Crear el entorno con [Poetry](https://python-poetry.org/):

```bash
poetry install
```

3. Configurar la base de datos PostgreSQL + PostGIS. El proyecto está configurado para usar Neon PostgreSQL.
4. Definir variables de entorno (crear archivo `.env`):

```env
POSTGRES_HOST=ep-red-fog-ad9w2fl1-pooler.c-2.us-east-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=tu_contraseña_aqui
POSTGRES_SSLMODE=require
```

5. Ejecutar migraciones y carga inicial:

```bash
# Crear las tablas en la base de datos
make db-init

# Cargar datos de obras desde el CSV
poetry run python tests/load_data.py

# Agregar coordenadas a algunas obras (opcional)
poetry run python scripts/seed_coordinates.py
```

6. Levantar la aplicación:

```bash
make run-dev
```

7. Acceso desde el navegador:
   - `http://localhost:5002/` → landing
   - `http://localhost:5002/obras/page` → catálogo de obras
   - `http://localhost:5002/autores/page` → catálogo de autores
   - `http://localhost:5002/mapa` → mapa interactivo
   - `http://localhost:5002/api/obras_geo` → API de obras georreferenciadas

## 5. Pruebas

Ejecutar la suite completa con:

```bash
make test
```

Las pruebas cubren:

- Repositorios SQL con filtros y paginación.
- Servicios con validación de parámetros.
- Rutas Flask (JSON y SSR).
- Casos con filtros inválidos, límites y escenarios vacíos.

## 6. Tecnologías utilizadas

- **Backend:** Python 3, Flask, PostgreSQL + PostGIS (consulta directa con psycopg2).
- **Frontend:** HTML + CSS (tipografía League Spartan) y Leaflet.js para el mapa.
- **Testing:** Pytest.
- **Dependencias:** Poetry.
- **Infraestructura:** Docker (opcional, disponible para desarrollo/CI si se configura).

## 7. Limitaciones del MVP

- Filtros básicos (autor, comuna, tipo, año, ubicación) sin búsqueda avanzada.
- No incluye autenticación ni CRUD para editar datos.
- UI sencilla enfocada en la funcionalidad principal.

## 8. Próximos pasos sugeridos

- Mejorar diseño responsivo y estilos globales.
- Agregar capas adicionales e interacción avanzada en el mapa.
- Implementar búsqueda avanzada y combinada en los catálogos.
- Documentar la API con Swagger/OpenAPI y exponer endpoints públicos.

---

## 💡 Autor

[Laura Sánchez Giraldo](mailto:laurasanchezgiraldo@outlook.es)
