# Resumen Ejecutivo: Sistema Inteligente de Pricing Klap

## Visión General

Este proyecto es un **pipeline de análisis de pricing** para Klap, un procesador de pagos chileno. Utiliza ciencia de datos para procesar datos transaccionales, segmentar comercios y generar estrategias de precios optimizadas. El sistema culmina en un dashboard interactivo para el equipo comercial.

---

## Arquitectura y Flujo de Datos

El sistema sigue un flujo de trabajo simple y efectivo:

1.  **Pipeline de Análisis (Jupyter Notebook)**: El notebook `pricing_22_10.ipynb` ejecuta el análisis principal. Realiza la ingeniería de características, calcula márgenes considerando costos (interchange), y segmenta a los comercios usando un modelo de clustering (K-means).
2.  **Salidas de Datos (Parquet)**: El notebook genera archivos `.parquet` que contienen los resultados del modelo, incluyendo la base de características de los comercios, los clusters asignados y las acciones sugeridas.
3.  **Dashboard Interactivo (Streamlit)**: La aplicación `app/streamlit_app.py` consume los archivos Parquet para presentar una interfaz web interactiva. Permite a los usuarios filtrar comercios, visualizar métricas clave y simular el impacto de nuevos escenarios de pricing.

---

## Estrategia y Valor para el Negocio

### Segmentación de Comercios

El modelo clasifica a los comercios en arquetipos accionables, tales como:
- **Alta contribución**: Comercios de alto valor y margen saludable.
- **Margen en riesgo**: Comercios con rentabilidad negativa o baja que requieren ajuste urgente.
- **Brecha competitiva**: Comercios con precios altos en comparación con competidores (ej. Transbank).
- **Baja actividad**: Comercios que necesitan una estrategia de reactivación.

### Valor Principal

- **Decisiones Basadas en Datos**: Reemplaza la intuición por un análisis sistemático para definir precios.
- **Optimización de Márgenes**: Identifica y permite corregir la rentabilidad de comercios no rentables.
- **Agilidad Comercial**: Proporciona al equipo comercial una herramienta para visualizar datos, simular escenarios y exportar propuestas de manera autónoma.
- **Automatización**: Reduce significativamente el tiempo de análisis manual.

---

## Componentes Técnicos

- **Lenguaje**: Python
- **Análisis de Datos**: Pandas, NumPy, Scikit-learn
- **Entorno de Desarrollo**: Jupyter Notebook
- **Dashboard**: Streamlit
- **Formato de Datos**: Parquet para un rendimiento eficiente.
