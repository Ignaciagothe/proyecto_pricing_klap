# Resumen de Cambios implementados

en notebook main_pricingklap.ipynb y otros scripts
#### Corrección 1: Campo de Volumen

**Problema:** Se usaba `monto_clp` (incluye ingresos no tarjeta) en vez de `monto_adquriencia_general` (solo volumen de tarjetas).

**Impacto:** 
- El 84% de las filas mostraban discrepancias.
- Brecha total: 8,58 billones CLP.
- Los cálculos de MDR y márgenes estaban inflados.

**Solución:**
- Se cambió la agregación a `monto_tarjetas` en todas las tablas y cálculos relevantes.




#### Corrección 2: Costos de Marca Reales (ACTUALIZADO)

**Problema:** Los costos de marca aparecían como 0% para Visa y Mastercard, lo que subestimaba los costos. Sin embargo, al aplicar los costos de 2025, se generaban márgenes negativos irreales.

**Causa Raíz:** Los costos en `costos_marca_25_1.xlsx` son proyecciones 2025, mientras que los datos transaccionales son de 2024. Los costos históricos son menores.

**Solución Implementada:**
- Se cargaron los costos de marca desde `costos_marca_25_1.xlsx` 
- Se aplicó **factor de ajuste histórico de 70%** para reflejar costos reales 2024
- Costos ajustados resultantes:
  - Mastercard: ~0.25-0.32% (vs 0.36-0.45% en 2025)
  - Visa: ~0.08-0.17% (vs 0.12-0.24% en 2025)
- Se agregó celda de validación que analiza comercios con margen negativo

**Fuente de Datos:**
- `costos_marca_25_1.xlsx` (proyecciones 2025)
- Factor de corrección: 0.70 (conservador, basado en tendencias históricas)

**IMPORTANTE:** Los comercios que aún muestren margen negativo después de este ajuste probablemente tienen:
1. Tarifas especiales no reflejadas en la grilla oficial
2. Mix de tarjetas atípico (alto débito)
3. Son genuinamente no rentables y requieren renegociación


#### Corrección 3: Integración del Modelo de Precios

**Problema:** El notebook nunca calculaba MDR, ingresos ni márgenes usando la grilla de precios real. (ups)

Los cálculos de margen estaban incompletos generaba resultados muy raros (como margenes negativos).

**Solución:**
- Se calculó MDR efectivo y fijo por segmento usando el esquema actrual de tarifas utilizado por Klap `Tarifas_Klap_2025.xlsx` en carpeta data.
- Ingresos y margen real historico por comercio.
- Recomendaciones generadas en base a margen, competitividad y actividad.

**Grilla aplicada:** (si tengo que cambiar esto pero es facil solo que no encontre la otra y me entro la duda)
- Estándar: MDR 0,974% | Fijo 95 CLP
- PRO: MDR 0,936% | Fijo 84 CLP
- PRO Max: MDR 0,936% | Fijo 80 CLP


#### Corrección 4: Métricas de riesgoo y tiempos de vida


**Problema:** No había análisis de churn ni clasificación de comercios por nivel de riesgo. Es decir, no se identificaban clientes en riesgo y pot lo tanto no se relaizaban las acciones proactivas necesarias.

**Solución:** Se implementó un marco de churn operacional con 5 categorías:

1. Churn Formal: Estado = BAJA/PROCESO_BAJA/BAJA_POR_PERDIDA
2. En alto riesgo: `share_meses_activos < 0,2` y `monto_max > 0`
3. Decreciente: `0,2 ≤ share < 0,5` y `monto_prom < 0,6 × monto_max`
4. Saludable: `share_meses_activos ≥ 0,7` y `margen ≥ 0`
5. Irregular: Otros casos

**Salidas:**
- Distribución por categoría de salud.
- Impacto financiero por categoría.
- Tablas cruzadas: churn vs. acciones sugeridas.
- Exportación de tabla de salud.


## Archivos de Datos Usados folder data in dir

- `costos_marca_25_1.xlsx`: Costos reales de marca por mes 2025.
- `Tarifas_Klap_2025.xlsx`: Grilla de precios 2025, 3 segmentos, tasas por tipo de tarjeta.
- `Tasa_Intercambio_Chile_Visa_y_Mastercard.csv`: Topes de tasa de intercambio para estimar costos mínimos.


- Falta aun incorporar al resto de los competidores en el anlaisis de precios de la competencia 
- utilizar variable MCC (tipo de comercio) para hacer la segmentacion


