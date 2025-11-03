# Modelo de Pricing Klap

**Versión**: 2.0 | **Actualización**: 2025-11-03

Este repositorio contiene codigo con modelamiento y la aplicación web para generar estrategia de pricing optimizada con los datos proporcionados.

## ✨ Características Principales (v2.0)

1. **Dashboard Ejecutivo** con KPIs estratégicos y sistema de alertas proactivas
2. **Planes predefinidos** con combinaciones fijo/MDR pensados para distintos patrones de uso
3. **Recomendaciones personalizadas** por comercio basadas en volumen, ticket medio, mix de marcas, márgenes y clusters
4. **Add-ons de alto valor** (omnicanal, fidelización, analytics) para capitalizar el multiservicio que ofrece Klap
5. **Simulador avanzado** con escenarios preconfigurados (Conservador, Agresivo, Premium)
6. **Matriz de priorización** automática de acciones comerciales
7. **Visualizaciones analíticas** (scatter plots, distribuciones, heatmaps)

## 🚨 Cambios Importantes en v2.0

⚠️ **CRÍTICO**: El archivo `data/precios_actuales_klap.xlsx` ahora es **OBLIGATORIO**. La app no tiene datos hardcodeados como fallback. Esto asegura que siempre uses la fuente única de verdad para tarifas oficiales.

Ver `CHANGELOG_v2.0.md` para detalles completos de cambios.


## Estructura principal

- `pricing_22_10.ipynb`: notebook que genera todas las métricas (márgenes, clusters, planes, add-ons). Debe ejecutarse cada vez que se actualicen datos transaccionales.
- `scripts/generate_pricing_proposals.py`: script opcional para regenerar únicamente las propuestas comerciales (`merchant_pricing_proposals.parquet`) después de haber generado los parquet base.
- `app/streamlit_app.py`: aplicación Streamlit para explorar resultados, simular ajustes de MDR/fijo y descargar propuestas por comercio.
- `app/requirements.txt`: dependencias necesarias para ejecutar la app/notebook.
- `data/`: carpeta local donde se almacenan los insumos y salidas (no se versiona).
- `.gitignore`: evita subir datos sensibles o artefactos locales.



## Ejecución
1. **Crear entorno**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r app/requirements.txt
   ```

2. **Colocar datos actualizados**
   - Tablas transaccionales limpias en `data/raw/` o `data/`.
   
3. **Regenerar métricas**
   - Abrir `pricing_22_10.ipynb` y ejecutar todas las celdas.
   - Se generarán:
     - `data/processed/merchant_pricing_feature_base.parquet`
     - `data/processed/merchant_pricing_model_results.parquet`
     - `data/processed/merchant_pricing_proposals.parquet`
   - Alternativa: ejecutar  

     ```bash
     python scripts/generate_pricing_proposals.py
     ```  

     (requiere que los dos primeros parquet ya existan).

## Uso de la app

### Despliegue

App deployed en:
<https://proyecto-titulo-pricing-klap.streamlit.app/>

### Ejecución Local

```bash
streamlit run app/streamlit_app.py
```

La app abrirá en `http://localhost:8501/`

### Estructura de Navegación (v2.0)

La nueva versión está organizada en 4 tabs principales:

#### 📊 **Tab 1: Dashboard Ejecutivo**
Vista estratégica para toma de decisiones rápidas:
- **KPIs principales**: Comercios totales, volumen anual, margen estimado, margen % promedio
- **Sistema de alertas**: Identifica automáticamente comercios con margen negativo, brecha competitiva alta, o alto valor inactivo
- **Matriz de priorización**: Score inteligente (0-100) que combina volumen, urgencia de margen y brecha competitiva
- **Visualizaciones**: Scatter plot margen vs volumen, distribución de gap competitivo

#### 🎯 **Tab 2: Análisis Detallado**
Análisis profundo para equipos comerciales y de producto:
- **Planes recomendados** con justificación automática (por qué se recomienda cada plan)
- **Distribución por acción sugerida** (tablas y gráficos)
- **Resumen por cluster analítico** con métricas agregadas
- **Exportación de datos** en CSV

#### 🎮 **Tab 3: Simulador de Escenarios**
Herramienta para evaluar impacto de cambios en tarifas:
- **Escenarios preconfigurados**:
  - 🟢 Conservador: -5bps MDR, -5 CLP fijo
  - 🟡 Igualar Transbank: -10bps MDR, -10 CLP fijo
  - 🔴 Agresivo: -20bps MDR, -20 CLP fijo
  - 💎 Incremento Premium: +10bps MDR, +10 CLP fijo
- **Simulación personalizada** con sliders
- **Comparación automática** actual vs simulado
- **Top 20 comercios más impactados** con deltas calculados

#### 📋 **Tab 4: Datos Completos**
Acceso completo a datos detallados:
- **Detalle por comercio** con todas las métricas
- **Mix de marcas** (Visa/Mastercard) con explicación de impacto
- **Exportación** de datos filtrados

### Funcionalidades Principales

- ✅ **Subir archivos Parquet** o usar los de `data/processed/`
- ✅ **Filtros avanzados**: por cluster, acción sugerida, plan comercial
- ✅ **Contador dinámico**: "Mostrando X de Y comercios"
- ✅ **Tooltips explicativos**: Hover sobre métricas para ver definiciones
- ✅ **Información temporal**: Muestra período de datos analizado
- ✅ **Exportación múltiple**: CSV de planes, detalle, comparaciones
- ✅ **Documentación integrada**: Sección expandible con definiciones y guías

## Flujo sugerido

1. **Identificar prioridad**  
   - En la app filtrar por cluster (ej. “Brecha competitiva”) o acción sugerida (ej. “Ajustar MDR urgente”).
   - Revisar el volumen y margen asociados al grupo.

2. **Revisión de plan recomendado**  
   - Confirmar que el plan propuesto tiene sentido con el comportamiento del comercio (ticket, volumen, tecnologías).
   - Ajustar con el simulador si se desea evaluar un MDR alternativo.

3. **Evaluar add-ons**  
   - Ver cuáles add-ons se sugieren (Omnicanal Plus, Insights & Fidelización, Pagos Internacionales) y comunicar la propuesta de valor asociada.

4. **Descargar lista y coordinar acción**  
   - Exportar CSV con el detalle filtrado.
   - Compartir con el ejecutivo comercial o integrarlo en campañas CRM.


Coordinar con BI la periodicidad de actualización (sugerido: mensual) y versionar los parquet para auditoría.

## Próximos pasos sugeridos

1. Incorporar precios reales pactados con cada comercio para medir margen observado vs. margen modelo.
2. Ajustar umbrales (`THRESHOLD_*`) con feedback del equipo comercial y resultados piloto.
3. Integrar datos de elasticidad o churn para reforzar decisiones de descuentos.
4. Evaluar autenticación y publicación interna (VPN o SSO) si se expone la app fuera del entorno controlado.



- *¿Si la app marca que falta un archivo?*  
  Ejecutar el notebook o el script del repositorio para generar los archivos y cargar los parquet.
- *¿Cambios en los posibles planes/add-ons?*  
  Sí. Edita la sección correspondiente en el notebook o en `scripts/generate_pricing_proposals.py` y regenera las tablas con los add-ons corregidos

