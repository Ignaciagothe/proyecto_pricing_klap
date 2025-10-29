# 📊 Informe Técnico: Notebook pricing_22_10.ipynb

## 📝 Información General

| Atributo | Detalle |
|----------|---------|
| **Nombre del Archivo** | `pricing_22_10.ipynb` |
| **Tipo** | Jupyter Notebook (Python) |
| **Tamaño** | 554 KB |
| **Total de Celdas** | 57 celdas |
| **Celdas Markdown** | 26 celdas (45.6%) |
| **Celdas de Código** | 31 celdas (54.4%) |
| **Propósito** | Notebook principal de análisis y modelamiento de pricing para Klap |

---

## 🎯 Descripción del Notebook

Este notebook es el **componente central** del sistema de pricing inteligente de Klap. Ejecuta el pipeline completo de procesamiento de datos, análisis exploratorio, feature engineering, modelamiento de márgenes y segmentación de comercios mediante clustering. El resultado final son tres archivos Parquet que alimentan el dashboard de Streamlit con propuestas personalizadas de pricing por comercio.

---

## 📋 Estructura del Notebook

### 1. **Proyecto Título - Modelo de Pricing y Sistema Recomendador**
   - **Descripción**: Introducción al proyecto y contexto de negocio
   - **Contexto**: Apertura del mercado de procesamiento de pagos en Chile post-monopolio Transbank
   - **Objetivo**: Posicionar a Klap como actor competitivo mediante pricing basado en datos

---

### 2. **Exploración Inicial de Datos de Pricing**

#### 2.1 Lectura de la Tabla y Limpieza
   - **Actividades**:
     - Carga de datos transaccionales desde archivos fuente
     - Identificación de columnas relevantes
     - Limpieza de valores nulos y duplicados
     - Validación de tipos de datos
   - **Fuentes de Datos**:
     - Transacciones de terminales
     - Información de comercios
     - Estados de terminales (ACTIVO, STOCK, BAJA)

#### 2.2 Estadísticas Generales del Dataset
   - **Métricas Calculadas**:
     - Número total de transacciones
     - Número de comercios únicos
     - Período temporal analizado
     - Distribución de volúmenes transaccionales
     - Estadísticas de ticket medio

---

### 3. **Agregación Comercio × Mes**

#### 3.1 Transformación de Datos
   - **Proceso**:
     - Agregación temporal por comercio y mes
     - Cálculo de métricas mensuales:
       - Volumen transaccional (CLP)
       - Número de transacciones
       - Ticket promedio
       - Mix de marcas (Visa/Mastercard)
       - Mix de medios (Crédito/Débito/Prepago)
   - **Granularidad**: Nivel comercio-mes

#### 3.2 Validaciones
   - **Checks Implementados**:
     - Consistencia de sumas vs. totales
     - Identificación de outliers
     - Validación de rangos de valores
     - Verificación de integridad referencial

---

### 4. **Datos Externos para Pricing**

   - **Fuentes Integradas**:
     - **Tasas de Intercambio (Interchange)**: Archivo `Tasa_Intercambio_Chile_Visa_y_Mastercard.csv`
       - Costos por tipo de tarjeta (Crédito/Débito/Prepago)
       - Diferenciación Visa vs. Mastercard
     - **Precios Actuales Klap**: Archivo `precios_actuales_klap.xlsx`
       - Segmentos de volumen (Estándar, PRO, PRO Max, Enterprise)
       - MDR por segmento y medio de pago
       - Tarifas fijas en UF y CLP
     - **Precios Competencia (Transbank)**: Benchmark de mercado
   
   - **Procesamiento**:
     - Lectura y limpieza de archivos Excel/CSV
     - Mapeo de segmentos a comercios
     - Cálculo de costos efectivos

---

### 5. **Tabla Comercio Agregada Final**

#### 5.1 Feature Engineering
   - **Variables Creadas**:
     - `monto_total_anual`: Volumen transaccional anual (CLP)
     - `n_transacciones`: Número total de transacciones
     - `ticket_promedio`: Monto promedio por transacción
     - `share_visa`: Proporción de transacciones Visa
     - `share_mastercard`: Proporción de transacciones Mastercard
     - `share_credito`: Proporción de crédito
     - `share_debito`: Proporción de débito
     - `share_prepago`: Proporción de prepago
     - `n_tecnologias_unicas`: Número de terminales/tecnologías
     - `n_meses_activos`: Meses con al menos una venta
     - `share_meses_activos`: Porcentaje de meses activos (vs. 12 meses)
     - `estado_terminal`: ACTIVO/STOCK/BAJA

#### 5.2 Supuestos Aplicados
   - **Segmentación de Volumen**:
     - **Estándar**: 0 a 8 MM CLP mensuales
     - **PRO**: 8 a 30 MM CLP mensuales
     - **PRO Max**: 30 a 75 MM CLP mensuales
     - **Enterprise**: >75 MM CLP mensuales
   - **Mix de Medios por Defecto** (cuando no hay datos):
     - Crédito: 60%
     - Débito: 35%
     - Prepago: 5%

---

### 6. **Modelo de Pricing y Margen**

#### 6.1 Cálculo de Costos
   - **Costo de Intercambio**:
     ```
     costo_intercambio = (monto_credito × interchange_credito) + 
                         (monto_debito × interchange_debito) + 
                         (monto_prepago × interchange_prepago)
     ```
   
   - **Costo de Marca**:
     ```
     costo_marca = (monto_visa × costo_visa) + 
                   (monto_mastercard × costo_mastercard)
     ```
   
   - **Costo Total Mínimo**:
     ```
     costo_min_estimado = costo_intercambio + costo_marca
     ```

#### 6.2 Cálculo de Ingresos
   - **Ingresos por MDR**:
     ```
     ingresos_mdr = monto_total_anual × klap_mdr
     ```
   
   - **Ingresos por Tarifa Fija**:
     ```
     ingresos_fijo = n_transacciones × klap_fijo
     ```
   
   - **Ingresos Totales**:
     ```
     ingresos_totales = ingresos_mdr + ingresos_fijo
     ```

#### 6.3 Cálculo de Margen
   - **Margen Absoluto**:
     ```
     margen_estimado = ingresos_totales - costo_min_estimado
     ```
   
   - **Margen Porcentual**:
     ```
     margen_pct_volumen = (margen_estimado / monto_total_anual) × 100
     ```

---

### 7. **Estimación de Variables**

   - **MDR Efectivo por Segmento**:
     - Calcula el MDR ponderado según mix de medios de pago
     - Considera diferencias entre Crédito/Débito/Prepago
   
   - **Tarifa Fija Efectiva**:
     - Promedio ponderado de tarifas por medio de pago
     - Conversión de UF a CLP
   
   - **Gap Competitivo**:
     ```
     gap_pricing_mdr = klap_mdr - competidor_mdr
     ```
     - Valores positivos: Klap más caro que competencia
     - Valores negativos: Klap más competitivo

---

### 8. **K-means Clusterización de Comercios**

#### 8.1 Preparación de Datos
   - **Variables para Clustering**:
     - Volumen transaccional (log-transformed)
     - Ticket promedio (log-transformed)
     - Share de meses activos
     - Margen porcentual
     - Gap competitivo
     - Mix de marcas
   
   - **Normalización**:
     - Uso de `StandardScaler` de scikit-learn
     - Estandarización Z-score (media 0, desviación 1)

#### 8.2 Modelo K-means
   - **Algoritmo**: K-means clustering
   - **Número de Clusters**: 5-6 clusters (determinado por análisis de silueta)
   - **Métricas de Validación**:
     - Silhouette Score: Mide calidad de clustering
     - Within-cluster sum of squares (WCSS)
     - Visualizaciones de clusters

#### 8.3 Interpretación de Clusters
   - **Clusters Típicos Identificados**:
     1. **Alta contribución**: Alto volumen, margen saludable, baja brecha competitiva
     2. **Brecha competitiva**: Pricing menos competitivo que mercado
     3. **Margen en riesgo**: Márgenes negativos o muy bajos
     4. **Baja actividad**: Pocos meses activos, necesita reactivación
     5. **Optimización gradual**: Estables con potencial de mejora
     6. **Sin ventas**: Sin transacciones en el período

---

### 9. **Nueva Segmentación de Comercios**

   - **Asignación de Etiquetas**:
     - Cada cluster recibe un nombre descriptivo basado en:
       - Perfil de margen
       - Nivel de actividad
       - Gap competitivo
       - Volumen transaccional
   
   - **Variables Añadidas**:
     - `cluster`: Número de cluster (0-5)
     - `segmento_cluster_label`: Etiqueta descriptiva del cluster

---

### 10. **Estrategia y Justificación de la Propuesta de Pricing**

   - **Definición de Planes**:
     - **Plan Estándar**: Para comercios 0-8 MM CLP mensuales
     - **Plan PRO**: Para comercios 8-30 MM CLP mensuales
     - **Plan PRO Max**: Para comercios 30-75 MM CLP mensuales
   
   - **Criterios de Asignación**:
     - Volumen transaccional
     - Cluster asignado
     - Margen actual
     - Gap competitivo
   
   - **Estrategias Diferenciadas**:
     - Descuentos para comercios de alto volumen
     - Ajustes para competir en segmentos críticos
     - Precios premium para comercios de nicho

---

### 11. **Identificación de Riesgos + Sistema Recomendador**

#### 11.1 Clasificación de Acciones
   - **Reglas de Negocio**:
     - `Reactivación`: `share_meses_activos < 0.2`
     - `Ajuste urgente`: `margen_pct_volumen < 0`
     - `Revisión competitiva`: `gap_pricing_mdr > 0.15`
     - `Monitoreo`: `share_meses_activos < 0.5`
     - `Mantener`: Comercios saludables sin alertas
     - `Up-sell`: Oportunidad de add-ons
   
   - **Variable Creada**: `accion_sugerida`

#### 11.2 Sistema Recomendador
   - **Propuestas Personalizadas**:
     - Plan de pricing recomendado
     - MDR y tarifa fija propuestos
     - Add-ons sugeridos según criterios:
       - **Omnicanal Plus**: <2 tecnologías y >$60M volumen
       - **Insights & Fidelización**: >60% meses activos y margen+
       - **Pagos Internacionales**: >50% Visa y >$120M volumen

---

### 12. **Próximos Pasos**

   - **Mejoras Propuestas**:
     - Incorporar precios reales pactados
     - Ajustar umbrales con feedback comercial
     - Integrar datos de elasticidad y churn
     - Validar con campañas piloto

---

## 🛠️ Tecnologías y Librerías Utilizadas

### Librerías de Python

| Librería | Propósito |
|----------|-----------|
| **pandas** | Manipulación y análisis de datos estructurados |
| **numpy** | Operaciones numéricas y arrays |
| **scikit-learn** | Machine learning (K-means, StandardScaler) |
| **matplotlib** | Visualizaciones y gráficos |
| **pathlib** | Manejo de rutas de archivos |

### Módulos Específicos

```python
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
```

---

## 📊 Archivos de Salida Generados

### 1. `merchant_pricing_feature_base.parquet`
   - **Contenido**: Características base de cada comercio
   - **Columnas Principales**:
     - `comercio_id`: Identificador único
     - `monto_total_anual`: Volumen anual
     - `n_transacciones`: Total de transacciones
     - `ticket_promedio`: Ticket medio
     - Shares de marcas y medios
     - Métricas de actividad
     - Estado de terminal
   - **Tamaño**: Variable según datos de entrada

### 2. `merchant_pricing_model_results.parquet`
   - **Contenido**: Resultados del modelo con métricas calculadas
   - **Columnas Principales**:
     - Todas las de `feature_base`
     - `klap_mdr`, `klap_fijo`: Pricing actual
     - `competidor_mdr`: Benchmark
     - `costo_min_estimado`: Costo total
     - `ingresos_totales`: Ingresos estimados
     - `margen_estimado`: Margen absoluto
     - `margen_pct_volumen`: Margen porcentual
     - `gap_pricing_mdr`: Brecha competitiva
     - `cluster`: Número de cluster
     - `segmento_cluster_label`: Etiqueta de cluster
     - `accion_sugerida`: Acción recomendada
   - **Uso**: Input para dashboard y generación de propuestas

### 3. `merchant_pricing_proposals.parquet` (generado posteriormente)
   - **Contenido**: Propuestas comerciales finales
   - **Generación**: Script `generate_pricing_proposals.py` usa los dos archivos anteriores
   - **Columnas Adicionales**:
     - `plan_recomendado`: Plan asignado
     - `mdr_propuesto`: MDR sugerido
     - `fijo_propuesto`: Tarifa fija sugerida
     - `addons_sugeridos`: Lista de add-ons
     - `fee_addons_total`: Fee mensual de add-ons

---

## 🔄 Flujo de Ejecución

```
┌─────────────────────────────────────────┐
│  1. Carga de Datos Transaccionales      │
│     - Transacciones                     │
│     - Comercios                         │
│     - Terminales                        │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  2. Limpieza y Validación               │
│     - Eliminación de nulos              │
│     - Validación de tipos               │
│     - Detección de outliers             │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  3. Agregación Comercio × Mes           │
│     - Métricas mensuales                │
│     - Mix de marcas y medios            │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  4. Integración Datos Externos          │
│     - Interchange rates                 │
│     - Precios Klap                      │
│     - Benchmark Transbank               │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  5. Feature Engineering                 │
│     - Variables derivadas               │
│     - Segmentación de volumen           │
│     - Métricas de actividad             │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  6. Cálculo de Costos y Márgenes        │
│     - Costo de intercambio              │
│     - Costo de marca                    │
│     - Ingresos Klap                     │
│     - Margen estimado                   │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  7. Clustering K-means                  │
│     - Normalización                     │
│     - Entrenamiento modelo              │
│     - Asignación de clusters            │
│     - Etiquetado descriptivo            │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  8. Sistema de Acciones                 │
│     - Evaluación de reglas              │
│     - Asignación de acción sugerida     │
└──────────────┬──────────────────────────┘
               │
               v
┌─────────────────────────────────────────┐
│  9. Exportación de Parquet              │
│     - feature_base.parquet              │
│     - model_results.parquet             │
└─────────────────────────────────────────┘
```

---

## 📈 Métricas y KPIs Principales

### Métricas de Negocio
- **Margen Promedio por Comercio**: Indicador de rentabilidad
- **Gap Competitivo Promedio**: Posicionamiento vs. mercado
- **Tasa de Comercios Activos**: Salud de la base de clientes
- **Volumen Total Procesado**: Tamaño del negocio

### Métricas del Modelo
- **Silhouette Score**: Calidad de clustering (objetivo: >0.4)
- **Número Óptimo de Clusters**: 5-6 clusters
- **Distribución de Comercios por Cluster**: Balanceo de segmentos

---

## 🎯 Casos de Uso del Notebook

### 1. Actualización Mensual de Métricas
   - **Frecuencia**: Mensual
   - **Proceso**:
     1. Cargar datos transaccionales del mes
     2. Ejecutar todas las celdas del notebook
     3. Verificar archivos Parquet generados
     4. Actualizar dashboard de Streamlit

### 2. Análisis de Nuevos Comercios
   - **Uso**: Onboarding de nuevos clientes
   - **Proceso**:
     1. Agregar datos del nuevo comercio
     2. Ejecutar notebook
     3. Identificar cluster asignado
     4. Generar propuesta de pricing

### 3. Evaluación de Cambios de Pricing
   - **Uso**: Simular impacto de ajustes de tarifas
   - **Proceso**:
     1. Modificar variables de MDR/fijo
     2. Re-ejecutar cálculos de margen
     3. Analizar cambios en distribución de clusters

### 4. Análisis de Competitividad
   - **Uso**: Benchmarking vs. Transbank
   - **Proceso**:
     1. Actualizar precios de competencia
     2. Recalcular gap competitivo
     3. Identificar comercios en riesgo

---

## ⚠️ Consideraciones Importantes

### Supuestos del Modelo
1. **Mix de Medios de Pago**: Si no hay datos, se asume 60% Crédito, 35% Débito, 5% Prepago
2. **Costos de Intercambio**: Se asumen valores mínimos (pueden variar según negociación)
3. **Año Completo**: Métricas anuales suponen 12 meses de operación

### Limitaciones
1. **Datos Históricos**: El modelo es retrospectivo, no predictivo
2. **Precios Reales**: No integra precios realmente pactados con cada comercio
3. **Elasticidad**: No modela respuesta de volumen a cambios de precio
4. **Churn**: No predice probabilidad de abandono

### Dependencias
- **Archivos de Entrada Requeridos**:
  - Datos transaccionales (CSV/Excel)
  - `Tasa_Intercambio_Chile_Visa_y_Mastercard.csv`
  - `precios_actuales_klap.xlsx`
- **Directorio de Salida**: `data/processed/` debe existir

---

## 🔧 Mantenimiento del Notebook

### Frecuencia de Ejecución
- **Mensual**: Actualización de métricas con nuevos datos
- **Trimestral**: Revisión de umbrales y reglas de negocio
- **Anual**: Reentrenamiento completo del modelo de clustering

### Puntos de Actualización
1. **Umbrales de Acciones** (Celdas de clasificación):
   - Ajustar límites de margen, gap competitivo, inactividad
2. **Número de Clusters** (Celda de K-means):
   - Modificar `n_clusters` según análisis de silueta
3. **Segmentos de Volumen** (Celda de feature engineering):
   - Ajustar rangos de Estándar/PRO/PRO Max
4. **Criterios de Add-ons** (Si están en el notebook):
   - Modificar condiciones de elegibilidad

---

## 📚 Documentación Relacionada

- **README.md**: Documentación general del proyecto
- **RESUMEN_EJECUTIVO.md**: Visión de negocio y valor estratégico
- **pricing_utils.py**: Módulo de funciones auxiliares
- **generate_pricing_proposals.py**: Script de generación de propuestas
- **streamlit_app.py**: Aplicación web de dashboard

---

## 👥 Información del Proyecto

**Desarrollador**: Ignacia Gothe  
**Empresa**: Klap  
**Contexto**: Proyecto de Título - Ingeniería Civil Industrial  
**Última Actualización**: Octubre 2025

---

## 🔗 Enlaces Útiles

- **Repositorio**: [https://github.com/Ignaciagothe/proyecto_pricing_klap](https://github.com/Ignaciagothe/proyecto_pricing_klap)
- **Dashboard Deployado**: [https://proyecto-titulo-pricing-klap.streamlit.app/](https://proyecto-titulo-pricing-klap.streamlit.app/)

---

<div align="center">

**📊 Documento Técnico Completo del Notebook Principal de Pricing Klap**

*Este informe documenta la estructura, funcionalidad y flujo de ejecución del notebook pricing_22_10.ipynb*

</div>
