# Modelo de Pricing Klap

Pipeline analítico y aplicación Streamlit para segmentar comercios, modelar márgenes y priorizar acciones de pricing en un adquirente de pagos.

## Contenido del repositorio

- `pricing_22_10.ipynb`: notebook principal con el EDA, generación de features, modelo de márgenes y segmentación mediante clustering.
- `pricing_10_20.ipynb`: exploraciones previas y utilidades de procesamiento.
- `app/streamlit_app.py`: aplicación Streamlit para explorar los resultados del modelo (márgenes, brecha competitiva, clusters, acciones sugeridas).
- `app/requirements.txt`: dependencias mínimas para ejecutar la app.
- `data/`: carpeta reservada para tablas de entrada/salida (no se versiona).
- `.gitignore`: excluye datos y artefactos locales.
