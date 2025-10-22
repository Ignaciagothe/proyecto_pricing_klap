# Modelo de Pricing Klap

Pipeline analítico y aplicación Streamlit para segmentar comercios, modelar márgenes y priorizar acciones de pricing en un adquirente de pagos.

## Contenido del repositorio

- `pricing_22_10.ipynb`: notebook principal con el EDA, generación de features, modelo de márgenes y segmentación mediante clustering.
- `pricing_10_20.ipynb`: exploraciones previas y utilidades de procesamiento.
- `app/streamlit_app.py`: aplicación Streamlit para explorar los resultados del modelo (márgenes, brecha competitiva, clusters, acciones sugeridas).
- `app/requirements.txt`: dependencias mínimas para ejecutar la app.
- `data/`: carpeta reservada para tablas de entrada/salida (no se versiona).
- `.gitignore`: excluye datos y artefactos locales.

## Requisitos

- Python 3.10+
- Pip o gestor de paquetes equivalente
- Opcional: entorno virtual (`python -m venv .venv`)

## Cómo reproducir el análisis

1. **Preparar el entorno**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r app/requirements.txt
   ```

2. **Ubicar los datos**  
   Copia los archivos CSV/Parquet fuentes dentro de `data/` respetando la estructura usada en el notebook (ej. `data/raw/`, `data/processed/`).

3. **Ejecutar el notebook**
   - Abre `pricing_22_10.ipynb`.
   - Corre todas las celdas para regenerar las tablas procesadas:
     - `data/processed/merchant_pricing_feature_base.parquet`
     - `data/processed/merchant_pricing_model_results.parquet`
   - Estas tablas alimentan la app.

## Ejecutar la app (local)

```bash
streamlit run app/streamlit_app.py
```

La aplicación se abrirá en `http://localhost:8501/`. Desde ahí puedes:
- Filtrar por cluster (`segmento_cluster_label`), acción sugerida o segmento de volumen.
- Revisar métricas agregadas (volumen, margen) y tablas por comercio.
- Consultar el mix de marcas (Visa/Mastercard) para complementar decisiones.

## Despliegue

1. **Control de versiones**
   ```bash
   git init
   git add .gitignore app README.md pricing_*.ipynb
   git commit -m "Primer commit"
   git branch -M main
   git remote add origin https://github.com/<usuario>/<repo>.git
   git push -u origin main
   ```

2. **Streamlit Cloud**
   - Sube un repositorio público con la estructura anterior.
   - En [share.streamlit.io](https://share.streamlit.io) crea una app nueva apuntando a `app/streamlit_app.py`.
   - Define la rama y asegúrate de que `app/requirements.txt` esté presente.
   - Para que la app acceda a los datos debes subir los Parquet necesarios (`merchant_pricing_feature_base.parquet`, `merchant_pricing_model_results.parquet`) o reconstruirlos en un paso previo dentro de la app.

3. **Alternativas (Docker/Cloud Run, etc.)**
   - Crea un Dockerfile que instale las dependencias y ejecute `streamlit run`.
   - Despliega en el servicio preferido (Cloud Run, EC2, Heroku) exponiendo el puerto 8501.

## Buenas prácticas

- Mantén los datos crudos fuera del repositorio (carpeta `data/` ignorada).
- Documenta cambios relevantes en el notebook colocando celdas markdown explicativas.
- Actualiza `app/requirements.txt` si agregas nuevas dependencias.
- Crea issues/tareas para experimentos adicionales (ej. nuevos benchmarks o simulaciones de elasticidad).

## Próximos pasos sugeridos

1. Incorporar precios reales por comercio para estimar márgenes observados vs. modelados.
2. Ajustar umbrales de acciones (`THRESHOLD_*`) con feedback del negocio.
3. Automatizar la actualización de parquet (job semanal/mensual) previo al despliegue.
4. Integrar autenticación en la app si se publica en un entorno compartido.

---

© 2024 Equipo de Pricing Klap. Proyecto interno para optimización de tarifas y segmentación de comercios.
