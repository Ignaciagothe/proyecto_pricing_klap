# 💰 Modelo de Pricing Inteligente - Klap

<div align="center">

**Sistema de Pricing Estratégico y Recomendación de Planes para Procesamiento de Pagos**

[![Streamlit App](https://img.shields.io/badge/Streamlit-Deployed-FF4B4B?style=for-the-badge&logo=streamlit)](https://proyecto-titulo-pricing-klap.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)

</div>

---

## 📋 Descripción del Proyecto

Este repositorio contiene un **sistema completo de análisis y optimización de pricing** desarrollado para **Klap**, empresa procesadora de pagos en el mercado chileno. El proyecto surge en el contexto de la apertura del mercado tras el fin del monopolio de Transbank, posicionando a Klap como un actor competitivo mediante estrategias de pricing basadas en datos.

### 🎯 Objetivos Principales

El sistema genera automáticamente:

1. **📊 Planes de Pricing Predefinidos**: Combinaciones optimizadas de MDR (Merchant Discount Rate) y tarifas fijas adaptadas a diferentes patrones de uso y volúmenes de transacción.

2. **🎯 Recomendaciones Personalizadas**: Propuestas individualizadas por comercio basadas en:
   - Volumen transaccional anual
   - Ticket medio de compra
   - Mix de marcas (Visa/Mastercard, Crédito/Débito/Prepago)
   - Análisis de márgenes y costos
   - Segmentación por clustering (K-means)

3. **🚀 Add-ons de Alto Valor**: Servicios complementarios estratégicos que capitalizan la propuesta multiservicios de Klap:
   - **Omnicanal Plus**: Integración con billeteras digitales, QR, web checkout y marketplaces
   - **Insights & Fidelización**: Reportes avanzados, programas de puntos, marketing SMS/Email
   - **Pagos Internacionales**: Aceptación de tarjetas internacionales y pagos cross-border

### 🔑 Valor Diferencial

El sistema permite a Klap incrementar ingresos tanto propios como de sus comercios mediante:
- Pricing competitivo y sostenible
- Identificación de brechas de mercado vs. competencia (principalmente Transbank)
- Segmentación inteligente de clientes
- Estrategias diferenciadas por cluster de comercio

---

## 📁 Estructura del Proyecto

```
proyecto_pricing_klap/
├── 📓 pricing_22_10.ipynb          # Notebook principal de análisis y modelamiento
├── 📓 pricing_25oct.ipynb          # Versión actualizada del notebook (octubre 2025)
├── 🐍 pricing_utils.py             # Módulo de utilidades y funciones auxiliares
├── 📂 scripts/
│   └── generate_pricing_proposals.py  # Script de generación de propuestas
├── 📂 app/
│   ├── streamlit_app.py            # Aplicación web interactiva
│   ├── requirements.txt            # Dependencias Python
│   └── .venv_pricing/              # Entorno virtual (no versionado)
├── 📂 data/
│   ├── precios_actuales_klap.xlsx  # Tabla de precios oficial de Klap
│   ├── raw/                        # Datos transaccionales crudos (no versionado)
│   └── processed/                  # Archivos Parquet generados (no versionado)
├── .gitignore                      # Excluye datos sensibles
└── README.md                       # Este archivo
```

---

## 📊 Componentes y Flujo de Trabajo

### 🔄 Pipeline de Datos

```
┌─────────────────────────┐
│ Datos Transaccionales   │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│  pricing_22_10.ipynb    │
│  - Feature Engineering  │
│  - Clustering KMeans    │
│  - Cálculo Márgenes     │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────────────────────┐
│  Archivos Parquet Generados:            │
│  • merchant_pricing_feature_base        │
│  • merchant_pricing_model_results       │
└───────────┬─────────────────────────────┘
            │
            v
┌─────────────────────────┐
│ generate_pricing_       │
│    proposals.py         │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ merchant_pricing_       │
│    proposals.parquet    │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│   streamlit_app.py      │
│  Dashboard Interactivo  │
└─────────────────────────┘
```

### 📘 Notebooks de Análisis

#### `pricing_22_10.ipynb` y `pricing_25oct.ipynb`
**Propósito**: Notebooks principales que ejecutan todo el pipeline de modelamiento.

**Contenido**:
- ✅ **Exploración de Datos (EDA)**: Análisis descriptivo de transacciones, terminales y comportamiento de comercios
- ✅ **Feature Engineering**: Creación de variables derivadas como:
  - Volumen anual y mensual
  - Ticket promedio
  - Mix de marcas y medios de pago
  - Tasas de actividad
  - Métricas de tecnología (número de terminales)
- ✅ **Cálculo de Costos**: 
  - Tasas de intercambio (interchange) por tipo de tarjeta
  - Costos de marca (Visa/Mastercard)
  - MDR efectivo por segmento
- ✅ **Modelo de Márgenes**: 
  - Ingresos totales estimados
  - Costos mínimos por comercio
  - Margen absoluto y porcentual
- ✅ **Clustering**: Segmentación de comercios en 5-6 clusters mediante K-means
- ✅ **Gap Analysis**: Comparación de pricing Klap vs. competidores (Transbank)
- ✅ **Sistema de Acciones**: Reglas de negocio para clasificar comercios en:
  - Reactivación
  - Ajuste urgente
  - Revisión competitiva
  - Monitoreo
  - Mantener/up-sell

**Salidas Generadas**:
1. `merchant_pricing_feature_base.parquet`: Características base de cada comercio
2. `merchant_pricing_model_results.parquet`: Resultados del modelo con clusters y acciones

---

### 🐍 Módulo `pricing_utils.py`

**Propósito**: Librería de funciones reutilizables para cálculos de pricing.

**Funciones Principales**:
- `compute_effective_rates()`: Calcula MDR y tarifa fija efectiva por segmento considerando mix de medios de pago
- `refresh_pricing_metrics()`: Recalcula métricas de margen y gap competitivo con ajustes de pricing
- Constantes configurables:
  - `ASSUMED_MIX_DEFAULT`: Mix por defecto de Crédito/Débito/Prepago
  - `FALLBACK_SEGMENTS_DEFAULT`: Mapeo de segmentos sin datos
  - `ACTION_THRESHOLDS_DEFAULT`: Umbrales para clasificación de acciones

**Uso**:
```python
from pricing_utils import compute_effective_rates

rates = compute_effective_rates("data/precios_actuales_klap.xlsx")
print(rates.mdr)  # Serie con MDR efectivo por segmento
print(rates.fijo)  # Serie con tarifa fija por segmento
```

---

### 🔧 Script `scripts/generate_pricing_proposals.py`

**Propósito**: Regenera únicamente las propuestas comerciales sin ejecutar todo el notebook.

**Uso**:
```bash
python scripts/generate_pricing_proposals.py
```

**Prerequisitos**: 
- Deben existir los archivos:
  - `merchant_pricing_feature_base.parquet`
  - `merchant_pricing_model_results.parquet`

**Funcionalidad**:
- 📋 Define 3 planes principales: Estándar, PRO, PRO Max
- 🎁 Asigna add-ons según criterios de volumen, actividad y mix de marcas
- 💡 Genera recomendaciones personalizadas por comercio
- 💾 Exporta `merchant_pricing_proposals.parquet`

**Add-ons Implementados**:

| Add-on | Fee Mensual | Criterio de Asignación |
|--------|-------------|------------------------|
| 🌐 Omnicanal Plus | $35,000 CLP | Comercios con <2 tecnologías y >$60M volumen anual |
| 📊 Insights & Fidelización | $25,000 CLP | Comercios con >60% meses activos y margen positivo |
| 🌍 Pagos Internacionales | $45,000 CLP | Comercios con >50% Visa y >$120M volumen anual |

---

### 🎨 Aplicación Streamlit `app/streamlit_app.py`

**Propósito**: Dashboard interactivo para exploración de resultados y simulación de escenarios.

**Deployed en**: [https://proyecto-titulo-pricing-klap.streamlit.app/](https://proyecto-titulo-pricing-klap.streamlit.app/)

**Funcionalidades**:

#### 📥 Carga de Datos
- Carga automática desde `data/processed/` si existe
- Opción de subir archivos Parquet personalizados
- Validación de estructura de datos

#### 🔍 Exploración y Filtrado
- **Filtros Disponibles**:
  - Cluster/Segmento (ej. "Alta contribución", "Brecha competitiva")
  - Acción sugerida (ej. "Ajuste urgente", "Reactivación")
  - Segmento de volumen (Estándar, PRO, PRO Max, Enterprise)
  - Rango de margen
  - Estado de terminal (ACTIVO, STOCK, BAJA)

#### 📊 Visualizaciones
- Distribución de comercios por cluster
- Análisis de márgenes por segmento
- Gap competitivo promedio
- Mix de marcas y medios de pago
- Métricas de actividad

#### 🎯 Planes Recomendados
- Visualización de plan asignado por comercio
- Detalle de MDR y tarifa fija propuestos
- Add-ons sugeridos con justificación

#### 🧮 Simulador de Pricing
- **Ajuste de MDR**: ±1.00 puntos porcentuales por cluster
- **Ajuste de Tarifa Fija**: ±$150 CLP por transacción
- **Cálculo en tiempo real**: Impacto en margen absoluto y porcentual
- **Visualización de diferencias**: Antes vs. Después

#### 📤 Exportación de Resultados
- Descarga de CSV con datos filtrados
- Incluye: comercio, plan recomendado, add-ons, métricas clave
- Formato listo para CRM o seguimiento comercial

---

## 🚀 Guía de Instalación y Ejecución

### 1️⃣ Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/Ignaciagothe/proyecto_pricing_klap.git
cd proyecto_pricing_klap

# Crear entorno virtual
python -m venv .venv

# Activar entorno
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r app/requirements.txt
```

**Dependencias principales**:
- `streamlit`: Framework de aplicación web
- `pandas`: Manipulación de datos
- `numpy`: Cálculos numéricos
- `pyarrow`: Lectura/escritura de Parquet
- `scikit-learn`: Clustering y machine learning
- `openpyxl`: Lectura de archivos Excel

---

### 2️⃣ Preparación de Datos

```bash
# Crear estructura de carpetas
mkdir -p data/raw data/processed

# Colocar datos transaccionales en data/raw/
# Archivos esperados:
# - Transacciones de terminales
# - Datos de comercios
# - Información de interchange
# - Precios competencia (opcional)
```

---

### 3️⃣ Ejecución del Pipeline

#### Opción A: Ejecución Completa (Recomendado)

```bash
# Abrir Jupyter Notebook
jupyter notebook

# Ejecutar pricing_22_10.ipynb (o pricing_25oct.ipynb)
# ✅ Run All Cells
```

**Archivos generados**:
- `data/processed/merchant_pricing_feature_base.parquet` (Features de comercios)
- `data/processed/merchant_pricing_model_results.parquet` (Resultados del modelo)
- `data/processed/merchant_pricing_proposals.parquet` (Propuestas comerciales)

#### Opción B: Regenerar Solo Propuestas

```bash
# Si ya tienes los archivos base generados
python scripts/generate_pricing_proposals.py
```

---

### 4️⃣ Lanzar Dashboard

```bash
# Iniciar aplicación Streamlit
streamlit run app/streamlit_app.py

# La app se abrirá en http://localhost:8501/
```

---

## 💼 Casos de Uso y Flujo Comercial

### 🎯 Caso 1: Identificación de Comercios en Riesgo

**Objetivo**: Detectar comercios con márgenes negativos o brechas competitivas críticas.

**Pasos**:
1. Abrir dashboard Streamlit
2. Filtrar por:
   - Cluster: "Margen en riesgo" 
   - Acción sugerida: "Ajuste urgente"
3. Revisar listado de comercios
4. Analizar métricas específicas:
   - Margen actual
   - Gap vs. competencia
   - Volumen transaccional
5. Aplicar simulador para proponer nuevo pricing
6. Exportar CSV con propuesta ajustada
7. Coordinar con equipo comercial para renegociación

---

### 🚀 Caso 2: Estrategia de Up-sell con Add-ons

**Objetivo**: Identificar comercios de alto valor para ofrecer servicios adicionales.

**Pasos**:
1. Filtrar por:
   - Cluster: "Alta contribución"
   - Margen: >5%
2. Revisar add-ons sugeridos por comercio
3. Priorizar por fee mensual potencial
4. Preparar pitch comercial basado en:
   - Beneficios del add-on
   - ROI estimado para el comercio
   - Casos de éxito similares
5. Exportar listado para campaña CRM
6. Hacer seguimiento de conversión

---

### 🔄 Caso 3: Reactivación de Comercios Inactivos

**Objetivo**: Recuperar comercios con baja actividad o sin ventas.

**Pasos**:
1. Filtrar por:
   - Acción sugerida: "Reactivación"
   - Estado terminal: "STOCK" o meses activos <20%
2. Analizar causas de inactividad:
   - Pricing no competitivo
   - Falta de tecnología (solo 1 terminal)
   - Estacionalidad del negocio
3. Diseñar estrategia diferenciada:
   - Descuento temporal en MDR
   - Oferta de terminal adicional
   - Capacitación en uso del sistema
4. Simular impacto en margen si reactivan
5. Exportar listado con propuesta personalizada

---

## 📊 Arquitectura de Datos

### 🗃️ Archivos Generados (data/processed/)

#### 1. `merchant_pricing_feature_base.parquet`

**Descripción**: Dataset con características base de cada comercio.

**Columnas principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comercio_id` | str | Identificador único del comercio |
| `monto_total_anual` | float | Volumen transaccional anual (CLP) |
| `n_transacciones` | int | Número total de transacciones |
| `ticket_promedio` | float | Monto promedio por transacción |
| `share_visa` | float | % de transacciones Visa |
| `share_credito` | float | % de transacciones crédito |
| `n_tecnologias_unicas` | int | Número de terminales/tecnologías |
| `share_meses_activos` | float | % de meses con ventas |
| `estado_terminal` | str | ACTIVO/STOCK/BAJA |
| `segmento_volumen` | str | Estándar/PRO/PRO Max/Enterprise |

---

#### 2. `merchant_pricing_model_results.parquet`

**Descripción**: Resultados del modelo de pricing con métricas calculadas.

**Columnas principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comercio_id` | str | Identificador único |
| `klap_mdr` | float | MDR actual de Klap (%) |
| `klap_fijo` | float | Tarifa fija actual (CLP) |
| `competidor_mdr` | float | MDR competidor de referencia (%) |
| `costo_min_estimado` | float | Costo mínimo por comercio (CLP) |
| `ingresos_totales` | float | Ingresos estimados de Klap (CLP) |
| `margen_estimado` | float | Margen absoluto (ingresos - costos) |
| `margen_pct_volumen` | float | Margen como % del volumen |
| `gap_pricing_mdr` | float | Diferencia Klap - Competidor (pp) |
| `cluster` | int | Número de cluster asignado (0-5) |
| `segmento_cluster_label` | str | Etiqueta descriptiva del cluster |
| `accion_sugerida` | str | Acción comercial recomendada |

**Clusters típicos**:
- 🏆 **Alta contribución**: Comercios de alto valor y margen saludable
- ⚠️ **Brecha competitiva**: Pricing menos competitivo que competencia
- 🔴 **Margen en riesgo**: Márgenes negativos o muy bajos
- 💤 **Baja actividad**: Pocos meses activos, necesita reactivación
- 📈 **Optimización gradual**: Estables, con potencial de mejora
- ⭕ **Sin ventas**: Sin transacciones en el período

**Acciones sugeridas**:
- `Reactivación`: Comercios inactivos
- `Ajuste urgente`: Márgenes negativos
- `Revisión competitiva`: Gap >0.15pp vs. competencia
- `Monitoreo`: Baja actividad pero no crítico
- `Mantener`: Comercios saludables
- `Up-sell`: Oportunidad de add-ons

---

#### 3. `merchant_pricing_proposals.parquet`

**Descripción**: Propuestas comerciales personalizadas por comercio.

**Columnas principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comercio_id` | str | Identificador único |
| `plan_recomendado` | str | Estándar/PRO/PRO Max |
| `plan_descripcion` | str | Descripción del plan |
| `mdr_propuesto` | float | MDR recomendado (%) |
| `fijo_propuesto` | float | Tarifa fija recomendada (CLP) |
| `addons_sugeridos` | list | Lista de add-ons aplicables |
| `fee_addons_total` | float | Fee mensual total de add-ons (CLP) |
| `justificacion` | str | Razón de la recomendación |

---

## 🔧 Configuración Avanzada

### ⚙️ Personalización de Umbrales

Editar en `pricing_utils.py`:

```python
ACTION_THRESHOLDS_DEFAULT = {
    "margin_threshold": 0.0,         # Margen mínimo aceptable (%)
    "competition_threshold": 0.0015, # Gap competitivo crítico (pp)
    "inactivity_threshold": 0.2,     # % meses activos mínimo
}
```

### 🎨 Modificación de Planes y Add-ons

Editar en `scripts/generate_pricing_proposals.py`:

```python
# Agregar nuevo plan
planes.append({
    "nombre": "Plan Premium",
    "segmento_origen": "Enterprise",
    "descripcion": "Plan exclusivo para grandes empresas",
    "segmentos_objetivo_volumen": ["Enterprise"],
    "segmentos_objetivo_cluster": ["Alta contribución"],
})

# Agregar nuevo add-on
ADDONS.append({
    "nombre": "Cashback Empresarial",
    "descripcion": "Programa de devolución de efectivo para empresas",
    "fee_mensual": 50000,
    "criterio": lambda row: row.get("monto_total_anual", 0) > 200_000_000,
})
```

---

## 📅 Mantenimiento y Actualización

### 🔄 Frecuencia Recomendada

**Mensual**: 
- Actualización de datos transaccionales
- Regeneración de archivos Parquet
- Revisión de clusters y ajuste de umbrales

**Trimestral**:
- Revisión de planes y add-ons
- Validación de efectividad de acciones sugeridas
- Ajuste de pricing de referencia

**Anual**:
- Reentrenamiento completo del modelo de clustering
- Actualización de tasas de intercambio
- Revisión estratégica de segmentación

---

### 📊 Auditoría y Versionado

```bash
# Crear snapshot de datos procesados
mkdir -p data/snapshots/2025-10-29
cp data/processed/*.parquet data/snapshots/2025-10-29/

# Documentar cambios en umbrales o reglas
git commit -m "Update pricing thresholds - Oct 2025"
```

---

## 🐛 Troubleshooting

### ❓ Problema: "No se encuentran archivos Parquet"

**Solución**:
```bash
# Ejecutar el notebook completo
jupyter notebook pricing_22_10.ipynb
# ✅ Run All Cells

# O regenerar propuestas
python scripts/generate_pricing_proposals.py
```

---

### ❓ Problema: "Clusters no tienen sentido comercial"

**Posibles causas**:
- Datos desactualizados o incompletos
- Número de clusters inadecuado (modificar `n_clusters` en notebook)
- Umbrales de segmentación mal calibrados

**Solución**:
1. Revisar calidad de datos de entrada
2. Ajustar parámetros de KMeans en el notebook
3. Validar interpretación de clusters con equipo comercial

---

### ❓ Problema: "App Streamlit no carga datos"

**Verificar**:
```bash
# Comprobar existencia de archivos
ls -lh data/processed/*.parquet

# Verificar permisos
chmod 644 data/processed/*.parquet

# Reiniciar app
streamlit run app/streamlit_app.py
```

---

### ❓ Problema: "Add-ons no se asignan correctamente"

**Depuración**:
```python
# En el notebook o script, activar modo debug
for addon in ADDONS:
    mask = df.apply(addon["criterio"], axis=1)
    print(f"{addon['nombre']}: {mask.sum()} comercios elegibles")
```

---

## 🚀 Roadmap y Mejoras Futuras

### 📋 Próximos Pasos Sugeridos

1. **📊 Integración de Datos Reales**
   - Incorporar precios pactados con cada comercio
   - Medir margen observado vs. margen modelo
   - Ajustar predicciones con data histórica de cambios de pricing

2. **🎯 Refinamiento de Modelo**
   - Ajustar umbrales (`THRESHOLD_*`) con feedback comercial
   - Incorporar resultados de campañas piloto
   - Entrenar modelo supervisado de churn prediction

3. **💡 Análisis Avanzado**
   - Integrar elasticidad precio-demanda
   - Modelar lifetime value por comercio
   - Análisis de sensibilidad de márgenes

4. **🔐 Seguridad y Despliegue**
   - Implementar autenticación (SSO, VPN)
   - Publicación interna en infraestructura corporativa
   - Logs de auditoría de cambios de pricing

5. **🤖 Automatización**
   - Pipeline automatizado de actualización (Airflow, Prefect)
   - Alertas automáticas de comercios en riesgo
   - Integración con CRM para seguimiento de propuestas

6. **📈 Nuevas Funcionalidades**
   - Simulador de escenarios de mercado
   - Benchmarking contra múltiples competidores
   - Análisis de canibalización entre planes

---

## 👥 Equipo y Contacto

**Desarrollado por**: Ignacia Gothe  
**Empresa**: Klap  
**Contexto**: Proyecto de Título - Ingeniería Civil Industrial  

**Repositorio**: [https://github.com/Ignaciagothe/proyecto_pricing_klap](https://github.com/Ignaciagothe/proyecto_pricing_klap)  
**App Deployada**: [https://proyecto-titulo-pricing-klap.streamlit.app/](https://proyecto-titulo-pricing-klap.streamlit.app/)

---

## 📄 Licencia

Este proyecto es propiedad de **Klap** y está destinado para uso interno corporativo.

---

## 🙏 Agradecimientos

Agradecimientos especiales al equipo de Klap por proporcionar los datos y el contexto de negocio necesarios para el desarrollo de este proyecto.

---

<div align="center">

**💳 Optimizando el futuro del procesamiento de pagos en Chile 🇨🇱**

</div>
