# Reporte Generación SEN 🇨🇱

Pipeline automatizado de análisis y reporte del mercado mayorista de electricidad chileno (SEN). Genera un reporte PowerPoint con gráficos, tablas y KPIs a partir de datos extraídos desde una base de datos MySQL, cubriendo vertimientos ERNC, costos marginales (CMG) y generación real.

---

## Descripción general

El pipeline extrae datos del mercado eléctrico chileno, los procesa con pandas, genera visualizaciones con matplotlib/seaborn y ensambla un reporte PowerPoint institucional listo para distribución en PDF. El proceso incluye una comparación entre el período de estudio y un período de referencia anterior.

```
MySQL (SSH tunnel)
    └→ pandas DataFrames
          ├→ Excel (respaldo de datos)
          └→ matplotlib/seaborn (gráficos PNG)
                └→ python-pptx (ensamblaje PPT)
                      └→ comtypes/PowerPoint (exportación PDF)
```

---

## Requisitos

- Python 3.11+
- Windows con Microsoft PowerPoint instalado (requerido para exportación PDF)
- Acceso SSH al servidor MySQL

### Dependencias Python

```bash
pip install pandas matplotlib seaborn geopandas openpyxl python-pptx paramiko comtypes
```

### Variables de entorno

Copia `.env.example` a `.env` y completa las credenciales:

```bash
cp .env.example .env
```

```env
# Conexión SSH
SSH_HOST=
SSH_USER=
SSH_KEY_PATH=

# Base de datos MySQL
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

---

## Estructura del proyecto

```
reporte_generacion/
├── main_reporte.py              # Punto de entrada principal
├── placerholders.py             # Utilidad para explorar shapes del PPT
├── .env.example                 # Plantilla de variables de entorno
├── data/
│   ├── raw/
│   │   ├── db/                  # CSVs cacheados (modo DEV)
│   │   └── templates/
│   │       └── template_reporte.pptx   # Plantilla PPT base (no modificar)
│   └── processed/
│       ├── images/              # PNGs generados por el pipeline
│       └── reports/             # PPT y PDF de salida
└── utils/
    ├── helpers.py               # Constantes y helpers de estilo
    ├── extrae_data.py           # Conexión MySQL y extracción de datos
    ├── gestiona_graficos.py     # Orquestador de gráficos
    ├── insercion_graficos.py    # Inserción de imágenes en PPT
    ├── inserta_texto_ppt.py     # Inserción de texto y KPIs en PPT
    ├── exporta_excel.py         # Exportación de DataFrames a Excel
    ├── calcula_gx_tipico.py     # Cálculo del día típico de generación
    ├── calcula_spread_cmg.py    # Cálculo de spread solar/no solar
    ├── calcula_gx_inyectada_vertida.py  # Balance inyección vs vertimiento
    ├── calcula_top_vertimiento.py       # Ranking de centrales por vertimiento
    ├── evoluciones_bess.py      # Evolución trimestral inyección BESS
    ├── evoluciones_vertimientos.py      # Evolución trimestral vertimientos
    └── graficos/                # Módulos de graficación individuales
        ├── grafico_cmg.py
        ├── grafico_dia_tipico.py
        ├── grafico_spread.py
        ├── grafico_boxplot.py
        ├── grafico_inyectada_vertida.py
        ├── grafico_bess.py
        └── grafico_evolucion_vertimiento.py
```

---

## Uso

### Modo producción (extrae desde MySQL)

```python
# En main_reporte.py
DEV = False
```

```bash
python main_reporte.py
```

### Modo desarrollo (usa CSVs cacheados)

```python
# En main_reporte.py
DEV = True
```

En la primera ejecución en modo producción los CSVs se guardan automáticamente en `data/raw/db/`. Las ejecuciones siguientes en modo DEV los reutilizan sin conectarse a la base de datos.

### Parámetros de fecha

Las fechas se configuran al final de `main_reporte.py`:

```python
fecha_inicio = "2025-01-01 00:00:00"
fecha_fin    = "2025-12-31 23:45:00"
```

El período de comparación se calcula automáticamente como un año antes.

---

## Gráficos generados

| Archivo                     | Descripción                                                    | Placeholder PPT                |
| --------------------------- | -------------------------------------------------------------- | ------------------------------ |
| `cmg.png`                   | CMG mensual por barra con mapa de Chile                        | `img_cmg`                      |
| `gx_tipico.png`             | Generación diaria típica (áreas apiladas, dos períodos)        | `img_dia_tipico`               |
| `spread_cmg.png`            | Spread CMG horas solares vs no solares                         | `img_spread`                   |
| `inyec_vert.png`            | Energía inyectada vs vertida por período                       | `img_inyecciones_vertimientos` |
| `inyecciones_bess.png`      | Evolución trimestral inyección BESS                            | `img_inyeccion_bess`           |
| `evolucion_vertimiento.png` | Evolución trimestral vertimientos                              | `img_evolucion_vertimientos`   |
| `tabla_top.png`             | Tabla con empresas que presentaron mayor vertimiento acumulado | `tabla_top`                    |

---

## Plantilla PowerPoint

La plantilla `template_reporte.pptx` **nunca debe modificarse directamente**. El pipeline copia la plantilla a `reporte_generacion.pptx` al inicio de cada ejecución.

### Placeholders de imagen

Los rectángulos de imagen en el PPT deben estar nombrados exactamente como indica la columna `Placeholder PPT` de la tabla anterior. Se pueden verificar con:

```bash
python placerholders.py
```

### Placeholders de texto

Los textos dinámicos usan la sintaxis `{{kpis.nombre_kpi}}`. Los KPIs disponibles son:

| Placeholder                                   | Descripción                             |
| --------------------------------------------- | --------------------------------------- |
| `{{kpis.vert_total_mwh}}`                     | Energía total vertida en el período     |
| `{{kpis.empresa_vert_max}}`                   | Central con mayor vertimiento acumulado |
| `{{kpis.vert_empresa_vert_max}}`              | Energía vertida por esa central         |
| `{{kpis.periodo_empresa_max}}`                | Mes de mayor vertimiento de esa central |
| `{{kpis.cmg_promedio}}`                       | CMG promedio del período ($/kWh)        |
| `{{kpis.cmg_max_mensual}}`                    | CMG máximo mensual ($/kWh)              |
| `{{kpis.cmg_max_mensual_periodo}}`            | Mes del CMG máximo                      |
| `{{kpis.cmg_spread_max_charrua}}`             | Spread máximo barra Crucero ($/kWh)     |
| `{{kpis.dia_cmg_spread_max_periodo_charrua}}` | Día del spread máximo Crucero           |
| `{{kpis.dia_cmg_spread_max_periodo_p_montt}}` | Spread máximo barra P. Montt ($/kWh)    |
| `{{kpis.barra_cmg_spread_max}}`               | Barra con mayor spread absoluto         |
| `{{kpis.nodo_cmg_spread_max}}`                | Nodo de la barra con mayor spread       |
| `{{kpis.fecha_perfil_1}}`                     | Fecha día típico período de estudio     |
| `{{kpis.fecha_perfil_2}}`                     | Fecha día típico período de comparación |

---

## Estilo visual

El reporte usa una paleta **Seaborn Muted** personalizada, consistente en todos los gráficos:

| Variable      | Valor     | Uso                             |
| ------------- | --------- | ------------------------------- |
| `c1`          | `#9EC8E8` | Año reciente / serie principal  |
| `c2`          | `#F4B89A` | Año anterior / serie secundaria |
| `c3`          | `#A8DDA5` | Verde salvia                    |
| `c4`          | `#E8A5A5` | Rojo arcilla                    |
| `c5`          | `#C4A8D4` | Violeta suave                   |
| `c6`          | `#C4A882` | Café rosado                     |
| `FONT_COLOR`  | `#003366` | Texto y ejes                    |
| `FONT_FAMILY` | `Candara` | Fuente global                   |

El archivo de tema Excel `SeabornMuted.thmx` está disponible para aplicar la misma paleta en hojas de cálculo.

### Escala de fuentes

Todas las funciones de graficación aceptan el parámetro `font_scale` para ajustar el tamaño de fuente proporcionalmente:

```python
font_scale=1.0   # tamaño base
font_scale=1.5   # 50% más grande
```

Se controla globalmente desde `generar_graficas()`.

---

## Outputs

Al finalizar la ejecución se generan dos archivos en `data/processed/reports/`:

- `reporte_generacion.pptx` — presentación editable
- `reporte_generacion.pdf` — versión para distribución

---

## Notas de desarrollo

- El modo `DEV = True` evita consultas a la base de datos usando los CSVs de la última extracción.
- El DPI de exportación de imágenes es `300` por defecto, calibrado para que las imágenes encajen exactamente en los placeholders sin escalado.
- El pipeline siempre parte desde `template_reporte.pptx` limpio — nunca acumula elementos de ejecuciones anteriores.
