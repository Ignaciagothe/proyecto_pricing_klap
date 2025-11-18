# Proyecto Pricing Klap

Sistema integral de análisis y recomendación de pricing para plataforma de pagos en mercado chileno.

## Contexto

Este proyecto surge en el contexto de la apertura del mercado de adquirencia en Chile, tras el fin del monopolio de Transbank. El desafío principal es posicionar a Klap como un actor competitivo en un entorno altamente regulado, con múltiples participantes y acceso limitado a información confiable del mercado.

El proyecto aborda la necesidad de establecer una estrategia de pricing fundamentada en datos que considere la estructura de costos del sector, el análisis competitivo, la segmentación de comercios, la estimación de márgenes y la identificación de riesgos de churn.

## Objetivos

### Objetivo General

Desarrollar un modelo de pricing dinámico y un sistema de recomendaciones que permita a Klap optimizar sus tarifas, maximizar rentabilidad y mejorar su competitividad en el mercado.

### Objetivos Específicos

1. **Análisis de Datos**: Consolidar y limpiar múltiples fuentes de datos transaccionales, tarifas y costos para construir una base analítica robusta.

2. **Modelado de Costos**: Estimar con precisión los costos de operación incluyendo tasas de intercambio y costos de marca (Visa, Mastercard) por comercio.

3. **Segmentación Estratégica**: Clasificar comercios mediante una matriz bidimensional (comportamiento × tamaño) para identificar micro-segmentos con necesidades específicas.

4. **Análisis Competitivo**: Calcular brechas de pricing contra competidores principales (especialmente Transbank) para cada segmento.

5. **Cálculo de Márgenes**: Determinar márgenes reales por comercio considerando ingresos (MDR + comisión fija) menos costos (intercambio + marca).

6. **Detección de Riesgo**: Identificar comercios con alto riesgo de churn basado en actividad, márgenes y patrones de uso.

7. **Generación de Propuestas**: Crear recomendaciones de planes y ajustes tarifarios accionables por segmento.

8. **Simulación de Escenarios**: Permitir simulación del impacto financiero de cambios tarifarios antes de implementación.

## Estructura del Repositorio

```
proyecto_pricing_klap/
│
├── main_pricingklap.ipynb          # Notebook principal con pipeline completo
├── pricing_utils.py                # Módulo de utilidades para cálculos de pricing
├── nueva_segmentacion.py           # Script de segmentación mejorada 2D
├── documentacion_cambios_recientes.md  # Log de correcciones importantes
│
├── data/                           # Datos de entrada (gitignored)
│   ├── Tarifas_Klap_2025.xlsx      # Grilla oficial de tarifas Klap
│   ├── precios_Competidores.xlsx   # Tarifas de competencia
│   ├── costos_marca_25_1.xlsx      # Costos reales de Visa/Mastercard
│   ├── Tasa_Intercambio_Chile_*.csv # Tasas de intercambio reguladas
│   ├── precios_actuales_klap.xlsx  # Precios actuales por segmento
│   └── processed/                  # Archivos parquet generados
│
├── app/                            # Aplicación Streamlit
│   ├── streamlit_app.py            # Dashboard interactivo
│   └── requirements.txt            # Dependencias de la app
│
└── scripts/                        # Scripts auxiliares
    ├── generate_pricing_proposals.py  # Generación de propuestas
    ├── analisis_churn_y_calidad.py    # Análisis de churn y validaciones
    └── clean_notebooks.sh              # Limpieza de outputs de notebooks
```

1. **Limpiar notebooks antes de commit**:
   ```bash
   ./scripts/clean_notebooks.sh
   ```

2. **Nunca subir a Git**:
   - Datos transaccionales (CSV/Excel con datos reales)
   - Notebooks con outputs ejecutados
   - Archivos parquet procesados
   - Credenciales o API keys

3. **Verificar antes de push**:
   ```bash
   git status
   git diff --cached
   ```


## Detalles de Implementación

### 1. Pipeline de Procesamiento de Datos

#### Fuente de Datos Principal

`base_con_sin_trx_cleaned.csv` contiene transacciones mensuales desagregadas por terminal y comercio. Dimensiones principales:

- **Temporales**: periodo mensual, fechas de instalación/baja
- **Identificadores**: RUT comercio, código local, número terminal
- **Métricas transaccionales**: volumen CLP, cantidad transacciones
- **Desglose por marca**: Visa, Mastercard, AMEX
- **Metadata**: estado terminal, tecnología, vertical, región

#### Correcciones Críticas Implementadas

**Corrección 1 - Campo de Volumen**

Problema: Se utilizaba `monto_clp` (incluye ingresos no tarjeta) en lugar de `monto_adquriencia_general` (solo tarjetas).

Impacto: 84% de filas con discrepancias, brecha total de 8.58 billones CLP.

Solución: Migración completa a `monto_adquriencia_general` como métrica base.

**Corrección 2 - Costos de Marca**

Problema: Costos de marca aparecían como 0% para Visa y Mastercard.

Solución: Integración de `costos_marca_25_1.xlsx`:
- Mastercard: 0.36% - 0.45%
- Visa: 0.12% - 0.24%

**Corrección 3 - Modelo de Precios**

Problema: No se calculaban MDR, ingresos ni márgenes con grilla real.

Solución: Módulo `pricing_utils.py` con funciones especializadas.

**Corrección 4 - Métricas de Riesgo**

Problema: No había análisis de churn ni clasificación por nivel de riesgo.

Solución: Marco de churn operacional con 5 categorías.

#### Agregación Comercio-Mes

```python
merchant_month = (
    df.groupby(["periodo", "rut_comercio"])
    .agg({
        "monto_adquriencia_general": "sum",  # Volumen de tarjetas
        "qtrx_total": "sum",
        "codigo_local": "nunique",
        "numero_terminal": "nunique"
    })
)
```

### 2. Módulo pricing_utils.py

Funciones principales:

**compute_effective_rates**: Calcula MDR y fijo efectivo por segmento considerando mix de medios de pago (60% crédito, 35% débito, 5% prepago).

**apply_effective_rates**: Asigna tarifas efectivas a cada comercio según su segmento.

**recompute_margin_metrics**: Recalcula ingresos y márgenes:
- Ingreso variable = volumen × MDR
- Ingreso fijo = cantidad_transacciones × fijo
- Margen = ingreso_total - costos

**recompute_action_labels**: Clasifica comercios en acciones sugeridas según umbrales de negocio.

### 3. Grilla de Tarifas

Tres segmentos principales (archivo `Tarifas_Klap_2025.xlsx`):

**Estándar** (0-8 MM CLP/mes):
- Crédito: 1.29% MDR + 95 CLP
- Débito: 0.57% MDR + 95 CLP
- Prepago: 0.99% MDR + 95 CLP

**PRO** (8-30 MM CLP/mes):
- Crédito: 1.24% MDR + 93 CLP
- Débito: 0.52% MDR + 77 CLP
- Prepago: 0.96% MDR + 77 CLP

**PRO Max** (30-75 MM CLP/mes):
- Crédito: 1.24% MDR + 89 CLP
- Débito: 0.52% MDR + 73 CLP
- Prepago: 0.96% MDR + 73 CLP

### 4. Sistema de Segmentación

#### Dimensión 1: Tamaño (por volumen)

Cinco niveles basados en volumen mensual promedio:

- **Estándar**: 0 - 5 MM CLP/mes
- **PRO**: 5 - 15 MM CLP/mes
- **PRO Max**: 15 - 40 MM CLP/mes
- **Enterprise**: 40 - 100 MM CLP/mes
- **Corporativo**: > 100 MM CLP/mes

#### Dimensión 2: Comportamiento (clustering)

Clustering K-Means con 6 clusters basado en:
- Volumen mensual promedio
- Margen porcentual
- Share de meses activos
- Gap competitivo
- Número de terminales

Etiquetas generadas:

1. **Champions**: Alto volumen + alto margen + alta actividad
2. **En Riesgo Crítico**: Margen negativo
3. **Potencial Alto**: Alto volumen, bajo margen (oportunidad)
4. **Brecha Competitiva**: Gap alto vs competencia
5. **Leales Rentables**: Volumen medio-alto + margen alto
6. **Inactivos Potencial**: Baja actividad, buen volumen potencial
7. **Básicos Estables**: Volumen bajo, margen estándar
8. **Optimización Gradual**: Resto

#### Matriz 2D Estratégica

Combinación de ambas dimensiones crea hasta 40 micro-segmentos, priorizando los que representan el 80% del volumen (regla de Pareto).

### 5. Análisis de Competencia

Benchmark principal: **Transbank**

Cálculo de gap competitivo:

```python
gap_pricing_mdr = klap_mdr - competidor_mdr
```

Umbrales de alerta:
- Gap > 15 bps (0.0015): Brecha alta
- Gap > 10 bps (0.0010): Brecha moderada
- Gap > 5 bps (0.0005): Brecha baja

### 6. Sistema de Acciones Sugeridas

Clasificación jerárquica según condiciones:

1. **Reactivación comercial**: Sin volumen en periodo
2. **Ajustar MDR urgente**: Margen negativo o muy bajo
3. **Revisar competitividad**: Gap > 15 bps vs Transbank
4. **Monitorear baja actividad**: < 20% meses activos
5. **Mantener / Upsell servicios**: Comercios saludables

### 7. Análisis de Churn

Marco operacional con 5 categorías:

1. **Churn Formal**: Estado = BAJA/PROCESO_BAJA/BAJA_POR_PERDIDA
2. **En alto riesgo**: share_meses_activos < 0.2 y monto_max > 0
3. **Decreciente**: 0.2 ≤ share < 0.5 y monto_prom < 0.6 × monto_max
4. **Saludable**: share_meses_activos ≥ 0.7 y margen ≥ 0
5. **Irregular**: Otros casos

Script `analisis_churn_y_calidad.py` genera reportes de salud por comercio y terminal.

### 8. Generación de Propuestas

Script `generate_pricing_proposals.py` produce archivo `merchant_pricing_proposals.parquet` con:

- Plan recomendado (Estándar / PRO / PRO Max)
- MDR y fijo propuesto
- Add-ons sugeridos (Omnicanal Plus, Insights, Pagos Internacionales)
- Justificación basada en perfil del comercio

### 9. Dashboard Interactivo (Streamlit)

`app/streamlit_app.py` proporciona:

**Dashboard Ejecutivo**:
- KPIs principales (volumen, margen, comercios)
- Alertas críticas automáticas

**Mapa de Segmentación**:
- Visualización de matriz 2D
- Distribución por comportamiento y tamaño
- Identificación de segmentos estratégicos

**Simulador de Escenarios**:
- Escenarios preconfigurados (Conservador, Igualar Transbank, Agresivo)
- Simulación personalizada de ajustes MDR y fijo
- Impacto proyectado en márgenes e ingresos

**Análisis por Comercio**:
- Búsqueda y filtrado individual
- Detalle completo de métricas
- Propuestas específicas

## Uso

### Ejecución del Notebook Principal

```bash
# Abrir notebook en Jupyter
jupyter notebook main_pricingklap.ipynb
```

El notebook ejecuta el pipeline completo:
1. Carga y limpieza de datos
2. Agregación comercio-mes
3. Cálculo de costos y márgenes
4. Segmentación 2D
5. Análisis competitivo
6. Generación de acciones
7. Exportación de resultados

### Generación de Propuestas

```bash
python scripts/generate_pricing_proposals.py
```

Genera archivo `data/processed/merchant_pricing_proposals.parquet`.

### Análisis de Churn

```bash
python scripts/analisis_churn_y_calidad.py \
    --base-csv base_con_sin_trx_cleaned.csv \
    --brand-costs data/costos_marca_25_1.xlsx \
    --output-dir data/processed
```

### Dashboard Interactivo

```bash
cd app
streamlit run streamlit_app.py
```

Acceder en http://localhost:8501

## Archivos de Datos Requeridos

### Obligatorios

- `base_con_sin_trx_cleaned.csv`: Base de transacciones
- `data/Tarifas_Klap_2025.xlsx`: Grilla oficial de tarifas
- `data/costos_marca_25_1.xlsx`: Costos de marca
- `data/Tasa_Intercambio_Chile_Visa_y_Mastercard.csv`: Tasas de intercambio

### Opcionales

- `data/precios_Competidores.xlsx`: Tarifas de competencia
- `data/precios_actuales_klap.xlsx`: Precios vigentes por segmento
- `data/precios_especiales.xlsx`: Excepciones negociadas
- `data/RUT_por_excluir_de_pricing.xlsx`: Comercios excluidos del análisis

## Dependencias

```
pandas
numpy
scikit-learn
matplotlib
streamlit
pyarrow
openpyxl
```

Instalar con:

```bash
pip install -r app/requirements.txt
```

## Outputs Generados

- `data/processed/merchant_pricing_model_results.parquet`: Resultados del modelo con todas las métricas
- `data/processed/merchant_pricing_feature_base.parquet`: Features agregadas por comercio
- `data/processed/merchant_pricing_proposals.parquet`: Propuestas de planes y add-ons
- `data/processed/merchant_health.csv`: Métricas de salud y churn por comercio
- `data/processed/terminal_health.csv`: Estado funcional de terminales

## Notas Técnicas

### Performance

- Dataset principal: ~1.4M filas (terminales × meses)
- Comercios únicos: ~75K
- Tiempo de ejecución notebook completo: ~5-10 minutos
- Dashboard: Carga datos en <5 segundos usando archivos parquet

### Limitaciones Conocidas

1. Mix de medios de pago asumido globalmente (ideal: calcular por comercio)
2. Costos de marca históricos estimados (requiere validación con datos reales)
3. Competencia limitada a 3 adquirentes (falta incorporar más competidores)
4. Segmentación no utiliza variable MCC (tipo de comercio) aún

### Próximos Desarrollos

- Incorporar variable MCC en segmentación
- Expandir análisis competitivo (más adquirentes)
- Integrar datos de costos operacionales directos
- Modelo predictivo de churn con ML
- API REST para integración con sistemas CRM

## Autor

Proyecto de Título IMC - Ignacia Gothe, Daniel Hidalgo
Contraparte - Klap
