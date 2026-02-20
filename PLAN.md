# Plan de Proyecto: Pipeline de Web Scraping E-commerce

## Información General

| Aspecto | Valor |
|---------|-------|
| **Categorías** | Laptops, Celulares, Televisores |
| **Fuente** | Mercado Libre México |
| **Productos/categoría** | 50-100 |
| **Motor BD** | SQLite |
| **Framework** | Scrapy |

---

## 1. Estructura del Proyecto

```
laboratorio-ecomerce/
├── data/
│   ├── raw/                    # Datos crudos (CSVs)
│   └── processed/              # Datos procesados
├── database/
│   ├── __init__.py
│   ├── db_manager.py           # Gestor de SQLite
│   └── ecommerce.db            # Base de datos SQLite (generado)
├── scraper/
│   ├── __init__.py
│   ├── settings.py             # Configuración Scrapy
│   ├── middlewares.py          # Rotación de User-Agents
│   ├── items.py                # Definición de items
│   ├── pipelines.py            # Pipeline de procesamiento
│   └── spiders/
│       ├── __init__.py
│       ├── laptops_spider.py
│       ├── celulares_spider.py
│       └── televisores_spider.py
├── analysis/
│   ├── __init__.py
│   └── queries.py              # Consultas SQL analíticas
├── main.py                     # Punto de entrada principal
├── requirements.txt
└── PLAN.md                     # Este archivo
```

---

## 2. Diseño de Base de Datos SQLite

### Tabla Principal: `productos`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Identificador único |
| `nombre` | TEXT NOT NULL | Nombre del producto |
| `precio_actual` | REAL | Precio actual (puede ser decimal) |
| `precio_anterior` | REAL | Precio anterior (NULL si no aplica) |
| `descuento_porcentaje` | INTEGER | Porcentaje de descuento (0-100) |
| `ubicacion_vendedor` | TEXT | Ciudad/región del vendedor |
| `cuotas` | INTEGER | Número de cuotas disponibles |
| `envio_gratis` | INTEGER (0/1) | Booleano: 1=gratis, 0=no gratis |
| `enlace` | TEXT UNIQUE | URL del producto (único) |
| `categoria` | TEXT NOT NULL | Categoría del producto |
| `fecha_extraccion` | TEXT | Fecha ISO (YYYY-MM-DD HH:MM:SS) |

### SQL de Creación:

```sql
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio_actual REAL,
    precio_anterior REAL,
    descuento_porcentaje INTEGER DEFAULT 0,
    ubicacion_vendedor TEXT,
    cuotas INTEGER DEFAULT 0,
    envio_gratis INTEGER DEFAULT 0,
    enlace TEXT UNIQUE,
    categoria TEXT NOT NULL,
    fecha_extraccion TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_categoria ON productos(categoria);
CREATE INDEX IF NOT EXISTS idx_precio ON productos(precio_actual);
CREATE INDEX IF NOT EXISTS idx_ubicacion ON productos(ubicacion_vendedor);
```

---

## 3. Estrategia Anti-Detección (Ética)

### Configuración en `settings.py`:

```python
# Respetar robots.txt
ROBOTSTXT_OBEY = True

# Delay entre requests (2-4 segundos aleatorios)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Limitar concurrencia
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Timeout
DOWNLOAD_TIMEOUT = 30

# Rotación de User-Agent
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    # ... más user agents
]

# Deshabilitar cookies
COOKIES_ENABLED = False
```

### Headers adicionales para parecer navegador real:

```python
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
}
```

---

## 4. Flujo del Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SPIDERS       │────▶│   PIPELINE      │────▶│   DATABASE      │
│  (Scraping)     │     │  (Procesamiento)│     │   (SQLite)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   Extraer datos           Validar/Limpiar        Almacenar
   - Nombre               - Parsear precios       - INSERT/UPDATE
   - Precios              - Calcular descuento    - Índices
   - Ubicación            - Formatear fechas
   - Cuotas
   - Envío
```

---

## 5. URLs Objetivo

| Categoría | URL |
|-----------|-----|
| Laptops | `https://listado.mercadolibre.com.mx/laptops` |
| Celulares | `https://listado.mercadolibre.com.mx/celulares` |
| Televisores | `https://listado.mercadolibre.com.mx/televisores` |

---

## 6. Consultas SQL Planificadas

### 1. Precio promedio por categoría
```sql
SELECT categoria, ROUND(AVG(precio_actual), 2) as precio_promedio
FROM productos
GROUP BY categoria;
```

### 2. Producto más costoso por categoría
```sql
SELECT * FROM productos p1
WHERE precio_actual = (
    SELECT MAX(precio_actual) FROM productos p2 
    WHERE p2.categoria = p1.categoria
);
```

### 3. Productos con envío gratis
```sql
SELECT COUNT(*) as total_envio_gratis
FROM productos
WHERE envio_gratis = 1;
```

### 4. Ubicación con más publicaciones
```sql
SELECT ubicacion_vendedor, COUNT(*) as total
FROM productos
GROUP BY ubicacion_vendedor
ORDER BY total DESC
LIMIT 1;
```

### 5. Descuento promedio por categoría
```sql
SELECT categoria, ROUND(AVG(descuento_porcentaje), 2) as descuento_promedio
FROM productos
WHERE precio_anterior IS NOT NULL
GROUP BY categoria;
```

### 6. Productos sobre precio promedio general
```sql
SELECT COUNT(*) as productos_sobre_promedio
FROM productos
WHERE precio_actual > (SELECT AVG(precio_actual) FROM productos);
```

### 7. Cinco productos más económicos por categoría
```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY categoria ORDER BY precio_actual ASC) as rn
    FROM productos WHERE precio_actual IS NOT NULL
) WHERE rn <= 5;
```

### 8. Ahorro promedio (cuando existe precio anterior)
```sql
SELECT ROUND(AVG(precio_anterior - precio_actual), 2) as ahorro_promedio
FROM productos
WHERE precio_anterior IS NOT NULL AND precio_actual IS NOT NULL;
```

### 9. Distribución por rangos de precio
```sql
SELECT 
    CASE 
        WHEN precio_actual < 5000 THEN 'Bajo (< $5,000)'
        WHEN precio_actual BETWEEN 5000 AND 15000 THEN 'Medio ($5,000-$15,000)'
        ELSE 'Alto (> $15,000)'
    END as rango,
    COUNT(*) as total
FROM productos
WHERE precio_actual IS NOT NULL
GROUP BY rango
ORDER BY total DESC;
```

---

## 7. Instrucciones de Uso

### Instalación:
```bash
pip install -r requirements.txt
```

### Ejecución completa:
```bash
python main.py
```

### Ejecución por fases:
```bash
# Solo scraping
python main.py --phase scrape

# Solo carga a BD
python main.py --phase load

# Solo análisis
python main.py --phase analyze
```

---

## 8. Estimación de Tiempo

| Fase | Tiempo estimado |
|------|-----------------|
| Configuración Scrapy | ~15 min |
| 3 Spiders | ~30 min |
| Pipeline + CSV | ~15 min |
| SQLite + Carga | ~15 min |
| 9 Consultas SQL | ~20 min |
| **Total** | **~1.5 horas** |
