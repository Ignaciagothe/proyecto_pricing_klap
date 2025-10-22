# Modelo de Pricing Klap 
Este repositorio contiene codigo con modelamiento y la aplicación web para generar estrategia de pricing optimizada con los datos proprcionados.

1. **Planes predefinidos** con combinaciones fijo/MDR pensados para distintos patrones de uso.
2. **Recomendaciones personalizadas** por comercio basadas en volumen, ticket medio, mix de marcas, márgenes y clusters.
3. **Add-ons de alto valor** (omnicanal, fidelización, analytics) para capitalizar el  multiservicio que ofrece klap, que es su pricipal ventaja comparativa. Se incrementar ingresos del comercio y de Klap.


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

## Uso de la app:


App deployed en:
<https://proyecto-titulo-pricing-klap.streamlit.app/>


Para ejecucion local:
```bash
streamlit run app/streamlit_app.py
```

La app abrirá en `http://localhost:8501/` y permite:

- **Subir archivos Parquet** o usar los que están en `data/processed/`.
- **Filtrar** por cluster (`segmento_cluster_label`), acción sugerida, segmento de volumen, etc.
- **Ver planes recomendados** (Plan Lite, Balanced, Enterprise Flex) con el MDR/fijo propuestos y los add-ons sugeridos para cada comercio.
- **Simular ajustes** de MDR y fijo por cluster para anticipar el efecto en márgenes antes de negociar.
- **Exportar listados** personalizados (detalles por comercio, plan recomendado, add-ons) y obtener un reporte ejecutivo listo para compartir.
- **Consultar métricas complementarias**: mix de marcas, estado actual de terminales, número de tecnologías, meses activos.

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

