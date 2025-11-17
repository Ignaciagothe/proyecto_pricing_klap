# ============================================================================
# NUEVA SEGMENTACIÓN MEJORADA: Matriz 2D Estratégica (6x5 = 30 micro-segmentos)
# ============================================================================

print("\n" + "="*80)
print("  MEJORA DE SEGMENTACIÓN: De 4 clusters básicos a Matriz Estratégica 2D")
print("="*80 + "\n")

# -----------------------------------------------------------------------------
# PASO 1: Aumentar granularidad de clustering (4 → 6 clusters)
# -----------------------------------------------------------------------------
print("📊 PASO 1: Re-clustering con 6 clusters para mayor granularidad\n")

k_mejorado = 6
kmeans_mejorado = KMeans(n_clusters=k_mejorado, random_state=42, n_init=20)
clusters_mejorado = kmeans_mejorado.fit_predict(seg_scaled)

# Asignar nuevos clusters
merchant_pricing_base.loc[mask_activos, "segmento_cluster_6"] = clusters_mejorado
merchant_pricing_base["segmento_cluster_6"] = (
    merchant_pricing_base["segmento_cluster_6"].fillna(-1).astype(int)
)

# Resumen estadístico de los 6 clusters
cluster_summary_6 = (
    merchant_pricing_base.loc[mask_activos]
    .groupby("segmento_cluster_6")
    .agg(
        n_comercios=("rut_comercio", "count"),
        monto_prom_mensual=("monto_promedio_mensual", "mean"),
        monto_total_millones=("monto_total_anual", lambda x: x.sum() / 1e6),
        share_activos_medio=("share_meses_activos", "mean"),
        margen_pct_medio=("margen_pct_volumen", "mean"),
        margen_estimado_millones=("margen_estimado", lambda x: x.sum() / 1e6),
        gap_mdr_medio=("gap_pricing_mdr", "mean"),
        n_terminales_promedio=("n_terminales_max", "mean"),
        klap_mdr_medio=("klap_mdr", "mean"),
    )
)

print(f"✅ Clustering completado: {k_mejorado} clusters creados")
print(f"   Total comercios activos: {mask_activos.sum():,}\n")

# -----------------------------------------------------------------------------
# PASO 2: Asignación de etiquetas mejoradas (más granulares y accionables)
# -----------------------------------------------------------------------------
print("🏷️  PASO 2: Asignación de etiquetas estratégicas\n")

# Umbrales dinámicos basados en distribución
vol_p75 = merchant_pricing_base.loc[mask_activos, "monto_promedio_mensual"].quantile(0.75)
vol_p50 = merchant_pricing_base.loc[mask_activos, "monto_promedio_mensual"].quantile(0.50)
vol_p25 = merchant_pricing_base.loc[mask_activos, "monto_promedio_mensual"].quantile(0.25)

margin_p75 = merchant_pricing_base.loc[mask_activos, "margen_pct_volumen"].quantile(0.75)
margin_p50 = merchant_pricing_base.loc[mask_activos, "margen_pct_volumen"].quantile(0.50)
margin_p25 = merchant_pricing_base.loc[mask_activos, "margen_pct_volumen"].quantile(0.25)

gap_p75 = merchant_pricing_base.loc[mask_activos, "gap_pricing_mdr"].quantile(0.75)
gap_p25 = merchant_pricing_base.loc[mask_activos, "gap_pricing_mdr"].quantile(0.25)

actividad_baja = 0.3  # <30% meses activos

labels_mejorado = {}
icons_segmento = {}
estrategia_segmento = {}

for cluster_id, row in cluster_summary_6.iterrows():
    vol = row["monto_prom_mensual"]
    margin = row["margen_pct_medio"]
    gap = row["gap_mdr_medio"]
    actividad = row["share_activos_medio"]
    margen_total = row["margen_estimado_millones"]

    # Reglas jerarquizadas (más específicas primero)

    # 1. CHAMPIONS: Alto volumen + Alto margen + Alta actividad
    if vol >= vol_p75 and margin >= margin_p75 and actividad >= 0.7:
        labels_mejorado[cluster_id] = "Champions"
        icons_segmento[cluster_id] = "⭐"
        estrategia_segmento[cluster_id] = "Mantener + Upsell premium"

    # 2. EN RIESGO CRÍTICO: Margen negativo
    elif margen_total <= 0:
        labels_mejorado[cluster_id] = "En Riesgo Crítico"
        icons_segmento[cluster_id] = "🚨"
        estrategia_segmento[cluster_id] = "Ajuste urgente o descontinuar"

    # 3. POTENCIAL ALTO: Alto volumen pero bajo margen (oportunidad)
    elif vol >= vol_p75 and margin < margin_p25:
        labels_mejorado[cluster_id] = "Potencial Alto"
        icons_segmento[cluster_id] = "🚀"
        estrategia_segmento[cluster_id] = "Optimizar pricing urgente"

    # 4. BRECHA COMPETITIVA: Gap alto vs competencia
    elif gap >= gap_p75 and gap > 0.0015:  # >15 bps
        labels_mejorado[cluster_id] = "Brecha Competitiva"
        icons_segmento[cluster_id] = "⚠️"
        estrategia_segmento[cluster_id] = "Ajustar a mercado"

    # 5. LEALES RENTABLES: Volumen medio-alto + margen alto + muy activos
    elif vol >= vol_p50 and margin >= margin_p50 and actividad >= 0.6:
        labels_mejorado[cluster_id] = "Leales Rentables"
        icons_segmento[cluster_id] = "💎"
        estrategia_segmento[cluster_id] = "Retener + Cross-sell"

    # 6. INACTIVOS CON POTENCIAL: Baja actividad pero con volumen cuando opera
    elif actividad < actividad_baja and vol >= vol_p25:
        labels_mejorado[cluster_id] = "Inactivos Potencial"
        icons_segmento[cluster_id] = "😴"
        estrategia_segmento[cluster_id] = "Reactivación + Incentivos"

    # 7. BÁSICOS: Volumen bajo + margen estándar
    elif vol < vol_p25 and margin >= margin_p25:
        labels_mejorado[cluster_id] = "Básicos Estables"
        icons_segmento[cluster_id] = "📊"
        estrategia_segmento[cluster_id] = "Mantener tarifas estándar"

    # 8. DEFAULT (resto)
    else:
        labels_mejorado[cluster_id] = "Optimización Gradual"
        icons_segmento[cluster_id] = "🔧"
        estrategia_segmento[cluster_id] = "Monitoreo + Ajustes selectivos"

# Aplicar etiquetas
cluster_summary_6["etiqueta_segmento"] = cluster_summary_6.index.map(labels_mejorado)
cluster_summary_6["icono"] = cluster_summary_6.index.map(icons_segmento)
cluster_summary_6["estrategia"] = cluster_summary_6.index.map(estrategia_segmento)

merchant_pricing_base["segmento_comportamiento"] = (
    merchant_pricing_base["segmento_cluster_6"]
    .map(labels_mejorado)
    .fillna("Sin ventas")
)

merchant_pricing_base["estrategia_comercial"] = (
    merchant_pricing_base["segmento_cluster_6"]
    .map(estrategia_segmento)
    .fillna("Reactivar cliente")
)

print("✅ Etiquetas asignadas a 6 clusters\n")

# -----------------------------------------------------------------------------
# PASO 3: Segmentación por tamaño (5 niveles en lugar de 4)
# -----------------------------------------------------------------------------
print("📏 PASO 3: Segmentación por tamaño (5 niveles)\n")

segment_bins_mejorado = [0, 5_000_000, 15_000_000, 40_000_000, 100_000_000, float("inf")]
segment_labels_mejorado = ["Estándar", "PRO", "PRO Max", "Enterprise", "Corporativo"]

merchant_pricing_base["segmento_tamaño"] = pd.cut(
    merchant_pricing_base["monto_promedio_mensual"],
    bins=segment_bins_mejorado,
    labels=segment_labels_mejorado,
    include_lowest=True,
).astype(str)

print("✅ Segmentación por tamaño completada")
print("   Rangos ajustados para mayor granularidad:\n")
for i, label in enumerate(segment_labels_mejorado):
    rango_min = f"${segment_bins_mejorado[i]/1e6:.1f}MM" if segment_bins_mejorado[i] > 0 else "$0"
    rango_max = f"${segment_bins_mejorado[i+1]/1e6:.1f}MM" if segment_bins_mejorado[i+1] != float("inf") else "+∞"
    print(f"   • {label:12s}: {rango_min:10s} - {rango_max}")

# -----------------------------------------------------------------------------
# PASO 4: Crear Matriz 2D (Comportamiento x Tamaño)
# -----------------------------------------------------------------------------
print("\n🎯 PASO 4: Creación de Matriz Estratégica 2D\n")

# Crear segmento combinado
merchant_pricing_base["segmento_matriz_2d"] = (
    merchant_pricing_base["segmento_comportamiento"] +
    " - " +
    merchant_pricing_base["segmento_tamaño"]
)

# Análisis de la matriz
matriz_segmentacion = merchant_pricing_base[
    merchant_pricing_base["monto_total_anual"] > 0
].groupby(["segmento_comportamiento", "segmento_tamaño"]).agg(
    n_comercios=("rut_comercio", "count"),
    volumen_total_mm=("monto_total_anual", lambda x: x.sum() / 1e6),
    margen_total_mm=("margen_estimado", lambda x: x.sum() / 1e6),
    margen_pct_promedio=("margen_pct_volumen", "mean"),
).reset_index()

# Calcular % de volumen y margen
total_vol = matriz_segmentacion["volumen_total_mm"].sum()
total_margin = matriz_segmentacion["margen_total_mm"].sum()

matriz_segmentacion["vol_share_pct"] = (
    matriz_segmentacion["volumen_total_mm"] / total_vol * 100
)
matriz_segmentacion["margin_share_pct"] = (
    matriz_segmentacion["margen_total_mm"] / total_margin * 100
)

# Identificar segmentos estratégicos (Pareto: 80% del valor)
matriz_segmentacion = matriz_segmentacion.sort_values(
    "volumen_total_mm", ascending=False
).reset_index(drop=True)

matriz_segmentacion["vol_cumsum_pct"] = matriz_segmentacion["vol_share_pct"].cumsum()
matriz_segmentacion["es_estrategico"] = matriz_segmentacion["vol_cumsum_pct"] <= 80

print(f"✅ Matriz 2D creada: {len(matriz_segmentacion)} micro-segmentos activos")
print(f"   Total volumen: ${total_vol:,.0f}MM")
print(f"   Total margen: ${total_margin:,.1f}MM\n")

# -----------------------------------------------------------------------------
# PASO 5: Visualización del resumen
# -----------------------------------------------------------------------------
print("=" * 80)
print("  RESUMEN DE SEGMENTACIÓN MEJORADA")
print("=" * 80 + "\n")

print("📊 Distribución por Comportamiento (6 clusters):\n")
comportamiento_resumen = cluster_summary_6[[
    "icono", "etiqueta_segmento", "n_comercios", "monto_total_millones",
    "margen_estimado_millones", "margen_pct_medio", "estrategia"
]].sort_values("monto_total_millones", ascending=False)

# Usar display si está disponible (Jupyter), sino print
try:
    display(comportamiento_resumen)
except NameError:
    print(comportamiento_resumen.to_string())

print("\n📏 Distribución por Tamaño:\n")
dist_tamaño = merchant_pricing_base[
    merchant_pricing_base["monto_total_anual"] > 0
].groupby("segmento_tamaño").agg(
    n_comercios=("rut_comercio", "count"),
    volumen_mm=("monto_total_anual", lambda x: x.sum() / 1e6),
    margen_mm=("margen_estimado", lambda x: x.sum() / 1e6),
)
try:
    display(dist_tamaño.sort_values("volumen_mm", ascending=False))
except NameError:
    print(dist_tamaño.sort_values("volumen_mm", ascending=False).to_string())

print("\n🎯 Top 10 Micro-Segmentos Estratégicos (Matriz 2D):\n")
top_matriz = matriz_segmentacion[[
    "segmento_comportamiento", "segmento_tamaño", "n_comercios",
    "volumen_total_mm", "margen_total_mm", "vol_share_pct", "es_estrategico"
]].head(10)
try:
    display(top_matriz)
except NameError:
    print(top_matriz.to_string())

print("\n" + "=" * 80)
print("✅ SEGMENTACIÓN MEJORADA COMPLETADA")
print("=" * 80)
print("\nPróximos pasos:")
print("1. Usar 'segmento_comportamiento' para estrategias comerciales")
print("2. Usar 'segmento_tamaño' para asignación de recursos")
print("3. Usar 'segmento_matriz_2d' para personalización granular")
print("4. Priorizar segmentos con 'es_estrategico' = True (regla 80/20)\n")
