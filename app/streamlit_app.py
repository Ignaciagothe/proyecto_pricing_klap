"""
Modelo de Pricing Klap - Dashboard Estratégico
================================================
Dashboard interactivo para análisis de pricing, segmentación de comercios,
simulación de escenarios y generación de propuestas comerciales.

Versión: 2.1
Fecha: 2025-11-17
Incluye ajuste histórico de costos de marca 2024
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ============================================================================
# CONFIGURACIÓN DE RUTAS E IMPORTS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pricing_utils import (  # noqa: E402
    ASSUMED_MIX_DEFAULT,
    FALLBACK_SEGMENTS_DEFAULT,
    compute_effective_rates,
    refresh_pricing_metrics,
    recompute_margin_metrics,
)

# Configuración de rutas de datos
DEFAULT_DATA_DIR = BASE_DIR / "data" / "processed"
DEFAULT_MODEL_FILE = DEFAULT_DATA_DIR / "merchant_pricing_model_results.parquet"
DEFAULT_FEATURE_FILE = DEFAULT_DATA_DIR / "merchant_pricing_feature_base.parquet"
DEFAULT_PROPOSALS_FILE = DEFAULT_DATA_DIR / "merchant_pricing_proposals.parquet"
PRICING_REFERENCE_FILE = BASE_DIR / "data" / "precios_actuales_klap.xlsx"

# Columnas requeridas para validación
REQUIRED_MODEL_COLS = {
    "rut_comercio",
    "segmento_cluster_label",
    "segmento_promedio_volumen",
    "accion_sugerida",
    "monto_total_anual",
    "margen_estimado",
    "margen_pct_volumen",
    "gap_pricing_mdr",
    "klap_mdr",
    "klap_fijo_clp",
    "competidor_mdr",
    "n_terminales_max",
    "n_tecnologias_unicas",
    "share_meses_activos",
    "costo_min_estimado",  # Crítico para validar cálculos de margen
}

# Columnas opcionales de la segmentación mejorada (si existen, se usan)
OPTIONAL_ENHANCED_COLS = {
    "segmento_comportamiento",
    "segmento_tamaño",
    "segmento_matriz_2d",
    "estrategia_comercial",
}

REQUIRED_PROPOSAL_COLS = {
    "plan_recomendado",
    "addons_recomendados",
    "plan_mdr_propuesto",
    "plan_fijo_propuesto",
}

# Escenarios preconfigurados para simulaciones
PRESET_SCENARIOS = {
    "Conservador": {
        "name": "Conservador",
        "description": "Ajuste mínimo para mantener competitividad",
        "mdr_delta": -0.05,  # -5 puntos base
        "fijo_delta": -5,  # -5 CLP
    },
    "Igualar Transbank": {
        "name": "Igualar Transbank",
        "description": "Equiparar tarifas con benchmark de mercado",
        "mdr_delta": -0.10,  # -10 puntos base
        "fijo_delta": -10,  # -10 CLP
    },
    "Agresivo": {
        "name": "Agresivo",
        "description": "Reducción significativa para capturar mercado",
        "mdr_delta": -0.20,  # -20 puntos base
        "fijo_delta": -20,  # -20 CLP
    },
    "Incremento Premium": {
        "name": "Incremento Premium",
        "description": "Aumento de tarifas en segmentos de alto valor",
        "mdr_delta": 0.10,  # +10 puntos base
        "fijo_delta": 10,  # +10 CLP
    },
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================


@st.cache_data(show_spinner=False)
def load_local_parquet(path: Path) -> pd.DataFrame:
    """Carga archivo Parquet con validación de existencia."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {path}")
    return pd.read_parquet(path)


def validate_required_columns(
    df: pd.DataFrame, required: set, data_name: str
) -> None:
    """Valida que el DataFrame contenga todas las columnas requeridas."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"❌ {data_name} falta las siguientes columnas requeridas:\n"
            f"{', '.join(sorted(missing))}\n\n"
            f"Regenera los archivos Parquet ejecutando el notebook completo."
        )


def load_pricing_reference() -> pd.DataFrame:
    """
    Carga archivo de referencia de precios oficiales de Klap.
    CRÍTICO: Falla si no existe - no usar fallbacks hardcodeados.
    """
    if not PRICING_REFERENCE_FILE.exists():
        raise FileNotFoundError(
            f"❌ No se encontró el archivo de precios oficiales:\n"
            f"{PRICING_REFERENCE_FILE}\n\n"
            f"Este archivo es CRÍTICO para el cálculo de tarifas.\n"
            f"Asegúrate de tenerlo en data/precios_actuales_klap.xlsx"
        )

    pricing_df = pd.read_excel(PRICING_REFERENCE_FILE)

    # Validar estructura
    required_cols = {"Segmento", "Medio", "Variable %", "Fijo CLP (aprox)"}
    missing = required_cols - set(pricing_df.columns)
    if missing:
        raise ValueError(
            f"❌ El archivo de precios no tiene la estructura correcta.\n"
            f"Columnas faltantes: {', '.join(missing)}"
        )

    return pricing_df


def load_sources(
    uploaded_model,
    uploaded_feature,
    uploaded_proposals,
    default_model: Path,
    default_feature: Path,
    default_proposals: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Carga datos desde archivos subidos o rutas por defecto con validaciones."""

    # Cargar modelo (obligatorio)
    if uploaded_model is not None:
        model_df = pd.read_parquet(uploaded_model)
        source = "Archivos cargados manualmente"
    elif default_model.exists():
        model_df = load_local_parquet(default_model)
        source = f"Ruta local: {default_model.name}"
    else:
        raise FileNotFoundError(
            "❌ No se encontró `merchant_pricing_model_results.parquet`.\n"
            "Ejecuta el notebook completo o sube un archivo para continuar."
        )

    # Validar columnas del modelo
    validate_required_columns(model_df, REQUIRED_MODEL_COLS, "Resultados del modelo")

    # Cargar features (obligatorio)
    if uploaded_feature is not None:
        feature_df = pd.read_parquet(uploaded_feature)
    elif default_feature.exists():
        feature_df = load_local_parquet(default_feature)
    else:
        raise FileNotFoundError(
            "❌ No se encontró `merchant_pricing_feature_base.parquet`.\n"
            "Ejecuta el notebook completo o sube un archivo para continuar."
        )

    # Cargar propuestas (opcional - puede generarse desde modelo)
    if uploaded_proposals is not None:
        proposal_df = pd.read_parquet(uploaded_proposals)
    elif default_proposals.exists():
        proposal_df = load_local_parquet(default_proposals)
    else:
        st.warning(
            "⚠️ No se encontró archivo de propuestas. "
            "Se usarán datos base sin recomendaciones específicas."
        )
        proposal_df = model_df.copy()
        for col in REQUIRED_PROPOSAL_COLS:
            if col not in proposal_df.columns:
                proposal_df[col] = "Sin información"

    return model_df, feature_df, proposal_df, source


def compute_period_info(df: pd.DataFrame) -> Dict[str, str]:
    """Extrae información temporal de los datos si está disponible."""
    info = {}

    # Buscar columnas temporales
    date_cols = [c for c in df.columns if 'fecha' in c.lower() or 'date' in c.lower()]

    if date_cols and len(df) > 0:
        try:
            dates = pd.to_datetime(df[date_cols[0]], errors='coerce').dropna()
            if len(dates) > 0:
                info['fecha_desde'] = dates.min().strftime('%Y-%m-%d')
                info['fecha_hasta'] = dates.max().strftime('%Y-%m-%d')
                info['periodo_meses'] = ((dates.max() - dates.min()).days / 30.44)
        except Exception:
            pass

    # Si no hay columnas de fecha, usar modificación del archivo
    if not info and DEFAULT_MODEL_FILE.exists():
        mod_time = datetime.fromtimestamp(DEFAULT_MODEL_FILE.stat().st_mtime)
        info['archivo_actualizado'] = mod_time.strftime('%Y-%m-%d %H:%M')

    return info


def format_currency(value: float) -> str:
    """Formatea valores monetarios con sufijos legibles."""
    if pd.isna(value):
        return "—"
    if abs(value) >= 1e9:
        return f"${value/1e9:,.2f}B"
    if abs(value) >= 1e6:
        return f"${value/1e6:,.2f}MM"
    if abs(value) >= 1e3:
        return f"${value/1e3:,.1f}K"
    return f"${value:,.0f}"


def format_percent(value: Optional[float]) -> str:
    """Formatea porcentajes con manejo de valores nulos."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value*100:.2f}%"


def format_basis_points(value: Optional[float]) -> str:
    """Formatea diferencias como puntos base."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value*10000:.0f} bps"


def compute_priority_score(row: pd.Series) -> float:
    """
    Calcula score de priorización (0-100) basado en:
    - Impacto: Volumen y margen
    - Urgencia: Gap competitivo y margen negativo
    """
    score = 0.0

    # Componente de volumen (0-40 puntos)
    volume = row.get('monto_total_anual', 0)
    if volume > 0:
        volume_percentile = min(volume / 100_000_000, 1.0)  # 100MM como referencia
        score += volume_percentile * 40

    # Componente de margen (0-30 puntos)
    margin_pct = row.get('margen_pct_volumen', 0)
    if margin_pct < 0:
        score += 30  # Margen negativo = urgente
    elif margin_pct < 0.005:
        score += 20  # Margen < 0.5% = alta prioridad
    elif margin_pct < 0.01:
        score += 10  # Margen < 1% = prioridad media

    # Componente de gap competitivo (0-30 puntos)
    gap = row.get('gap_pricing_mdr', 0)
    if gap > 0.002:  # > 20 bps
        score += 30
    elif gap > 0.001:  # > 10 bps
        score += 20
    elif gap > 0.0005:  # > 5 bps
        score += 10

    return min(score, 100)


def apply_simulation(
    df: pd.DataFrame,
    target_segments: List[str],
    mdr_delta: float,
    fijo_delta: float,
    segment_column: str = "segmento_cluster_label",
) -> pd.DataFrame:
    """
    Aplica simulación de ajuste de tarifas usando funciones de pricing_utils.
    Elimina duplicación de lógica.

    Args:
        df: DataFrame con datos de comercios
        target_segments: Lista de segmentos a afectar
        mdr_delta: Cambio en MDR (puntos porcentuales)
        fijo_delta: Cambio en fijo (CLP)
        segment_column: Columna a usar para identificar segmentos
    """
    result = df.copy()

    # Identificar comercios afectados (usar columna especificada)
    if segment_column not in result.columns:
        segment_column = "segmento_cluster_label"  # Fallback
    mask = result[segment_column].isin(target_segments)

    # Aplicar deltas a tarifas
    result["klap_mdr_sim"] = result["klap_mdr"].copy()
    result["klap_fijo_sim"] = result["klap_fijo_clp"].copy()

    result.loc[mask, "klap_mdr_sim"] = result.loc[mask, "klap_mdr"] + (mdr_delta / 100)
    result.loc[mask, "klap_fijo_sim"] = result.loc[mask, "klap_fijo_clp"] + fijo_delta

    # Usar funciones de pricing_utils para recalcular métricas
    # (evita duplicación de fórmulas)
    result_sim = result.copy()
    result_sim["klap_mdr"] = result_sim["klap_mdr_sim"]
    result_sim["klap_fijo_clp"] = result_sim["klap_fijo_sim"]

    # Recalcular márgenes con tarifas simuladas
    result_sim = recompute_margin_metrics(
        result_sim,
        volume_col="monto_total_anual",
        qtrx_col="qtrx_total_anual",
        cost_col="costo_min_estimado",
        mdr_col="klap_mdr",
        fijo_col="klap_fijo_clp",
    )

    # Copiar resultados simulados con sufijo
    result["margen_estimado_sim"] = result_sim["margen_estimado"]
    result["margen_pct_volumen_sim"] = result_sim["margen_pct_volumen"]
    result["ingreso_total_sim"] = result_sim["ingreso_total_klap"]

    return result


# ============================================================================
# COMPONENTES DE VISUALIZACIÓN
# ============================================================================


def render_executive_dashboard(df: pd.DataFrame, period_info: Dict[str, str]) -> None:
    """Renderiza dashboard ejecutivo con KPIs principales."""
    st.markdown("## 📊 Dashboard Ejecutivo")

    # Información temporal
    if 'fecha_desde' in period_info:
        st.caption(
            f"📅 Período analizado: {period_info['fecha_desde']} a {period_info['fecha_hasta']} "
            f"({period_info['periodo_meses']:.0f} meses)"
        )
    elif 'archivo_actualizado' in period_info:
        st.caption(f"📅 Datos actualizados: {period_info['archivo_actualizado']}")

    st.markdown("---")

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    total_comercios = len(df)
    total_volumen = df["monto_total_anual"].sum()
    total_margen = df["margen_estimado"].sum()
    margen_pct_promedio = df["margen_pct_volumen"].mean()

    col1.metric(
        "Comercios totales",
        f"{total_comercios:,}",
        help="Total de comercios en el análisis"
    )

    col2.metric(
        "Volumen anual",
        format_currency(total_volumen),
        help="Suma de volumen transaccional anualizado de todos los comercios"
    )

    col3.metric(
        "Margen estimado",
        format_currency(total_margen),
        delta=f"{(total_margen/total_volumen)*100:.2f}% del volumen" if total_volumen > 0 else None,
        help="Margen = Ingresos (MDR + fijo) - Costos mínimos (interchange + marca)"
    )

    col4.metric(
        "Margen % promedio",
        format_percent(margen_pct_promedio),
        help="Promedio simple del margen % sobre volumen de todos los comercios"
    )

    st.markdown("---")

    # Alertas críticas
    st.markdown("### 🚨 Alertas Críticas")

    alertas = []

    # Comercios con margen negativo
    margen_negativo = df[df["margen_estimado"] < 0]
    if len(margen_negativo) > 0:
        vol_riesgo = margen_negativo["monto_total_anual"].sum()
        pct_comercios = len(margen_negativo) / len(df) * 100
        alertas.append({
            "nivel": "🔴",
            "tipo": "Margen Negativo",
            "cantidad": len(margen_negativo),
            "volumen": vol_riesgo,
            "descripcion": (
                f"{len(margen_negativo)} comercios con margen negativo "
                f"({pct_comercios:.1f}% del total, {format_currency(vol_riesgo)} en volumen). "
                f"Probable causa: tarifas especiales no capturadas o mix de tarjetas atípico."
            )
        })

    # Comercios con brecha competitiva alta
    brecha_alta = df[df["gap_pricing_mdr"] > 0.0015]  # >15 bps
    if len(brecha_alta) > 0:
        vol_brecha = brecha_alta["monto_total_anual"].sum()
        alertas.append({
            "nivel": "🟠",
            "tipo": "Brecha Competitiva Alta",
            "cantidad": len(brecha_alta),
            "volumen": vol_brecha,
            "descripcion": f"{len(brecha_alta)} comercios >15bps sobre Transbank ({format_currency(vol_brecha)} en volumen)"
        })

    # Comercios inactivos de alto valor
    alto_valor_inactivo = df[
        (df["monto_total_anual"] > 10_000_000) &  # >10MM CLP
        (df["share_meses_activos"] < 0.3)  # <30% meses activos
    ]
    if len(alto_valor_inactivo) > 0:
        alertas.append({
            "nivel": "🟡",
            "tipo": "Alto Valor Inactivo",
            "cantidad": len(alto_valor_inactivo),
            "volumen": alto_valor_inactivo["monto_total_anual"].sum(),
            "descripcion": f"{len(alto_valor_inactivo)} comercios de alto valor con baja actividad (riesgo de churn)"
        })

    if alertas:
        for alerta in alertas:
            st.warning(
                f"{alerta['nivel']} **{alerta['tipo']}**: {alerta['descripcion']}"
            )
    else:
        st.success("✅ No hay alertas críticas en este momento")

    st.markdown("---")


def render_action_prioritization(df: pd.DataFrame) -> None:
    """Renderiza matriz de priorización de acciones."""
    st.markdown("### 🎯 Priorización de Acciones")

    # Calcular score de prioridad
    df_prior = df.copy()
    df_prior["score_prioridad"] = df_prior.apply(compute_priority_score, axis=1)

    # Agrupar por acción sugerida
    action_summary = df_prior.groupby("accion_sugerida").agg({
        "rut_comercio": "count",
        "monto_total_anual": "sum",
        "margen_estimado": "sum",
        "score_prioridad": "mean",
    }).reset_index()

    action_summary.columns = [
        "Acción",
        "Comercios",
        "Volumen",
        "Margen",
        "Score Prioridad"
    ]

    # Ordenar por score de prioridad
    action_summary = action_summary.sort_values("Score Prioridad", ascending=False)

    # Asignar nivel de prioridad
    def assign_priority_level(score):
        if score >= 70:
            return "🔴 Crítico"
        elif score >= 50:
            return "🟠 Alto"
        elif score >= 30:
            return "🟡 Medio"
        else:
            return "🟢 Bajo"

    action_summary["Prioridad"] = action_summary["Score Prioridad"].apply(assign_priority_level)

    # Reordenar columnas
    action_summary = action_summary[[
        "Prioridad",
        "Acción",
        "Comercios",
        "Volumen",
        "Margen",
        "Score Prioridad"
    ]]

    st.dataframe(
        action_summary.style.format({
            "Volumen": format_currency,
            "Margen": format_currency,
            "Score Prioridad": "{:.1f}",
        }).background_gradient(subset=["Score Prioridad"], cmap="RdYlGn"),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "💡 **Score de Prioridad**: Calculado considerando volumen (40%), urgencia de margen (30%) "
        "y brecha competitiva (30%). Score >70 = acción crítica."
    )


def render_segmentation_map(df: pd.DataFrame) -> None:
    """Renderiza mapa estratégico de segmentación mejorada."""

    # Verificar si existen las columnas de segmentación mejorada
    tiene_segmentacion_mejorada = all(
        col in df.columns
        for col in ["segmento_comportamiento", "segmento_tamaño", "estrategia_comercial"]
    )

    if not tiene_segmentacion_mejorada:
        st.info(
            "💡 **Segmentación mejorada no disponible**\n\n"
            "Para habilitar la vista de Mapa Estratégico, ejecuta el notebook completo "
            "con la nueva segmentación 2D (celdas 44-45)."
        )
        return

    st.markdown("### 🗺️ Mapa Estratégico de Segmentación")

    st.markdown("""
    **Matriz 2D**: Combina **Comportamiento** (cómo operan los comercios) × **Tamaño** (volumen transaccional)
    para crear **micro-segmentos** con estrategias específicas.
    """)

    # Métricas globales
    comercios_activos = df[df["monto_total_anual"] > 0]

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Comercios activos",
        f"{len(comercios_activos):,}",
        help="Comercios con ventas en el período"
    )
    col2.metric(
        "Tipos de Comportamiento",
        comercios_activos["segmento_comportamiento"].nunique(),
        help="Clusters de comportamiento identificados"
    )
    col3.metric(
        "Niveles de Tamaño",
        comercios_activos["segmento_tamaño"].nunique(),
        help="Rangos de volumen transaccional"
    )

    st.markdown("---")

    # Distribución por comportamiento
    st.markdown("#### 🎯 Segmentación por Comportamiento")

    comportamiento_summary = comercios_activos.groupby("segmento_comportamiento").agg(
        comercios=("rut_comercio", "count"),
        volumen=("monto_total_anual", "sum"),
        margen=("margen_estimado", "sum"),
        margen_pct=("margen_pct_volumen", "mean"),
    ).reset_index()

    comportamiento_summary = comportamiento_summary.sort_values("volumen", ascending=False)

    # Calcular % del total
    total_vol = comportamiento_summary["volumen"].sum()
    total_margin = comportamiento_summary["margen"].sum()
    comportamiento_summary["vol_share"] = (
        comportamiento_summary["volumen"] / total_vol * 100
    )
    comportamiento_summary["margin_share"] = (
        comportamiento_summary["margen"] / total_margin * 100
    )

    # Agregar estrategia (tomar la más frecuente por segmento)
    estrategias = comercios_activos.groupby("segmento_comportamiento")["estrategia_comercial"].agg(
        lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]
    )
    comportamiento_summary["estrategia"] = comportamiento_summary["segmento_comportamiento"].map(estrategias)

    st.dataframe(
        comportamiento_summary[[
            "segmento_comportamiento", "comercios", "volumen", "margen",
            "vol_share", "margen_pct", "estrategia"
        ]].style.format({
            "volumen": format_currency,
            "margen": format_currency,
            "vol_share": "{:.1f}%",
            "margen_pct": "{:.2%}",
        }).background_gradient(subset=["vol_share"], cmap="YlOrRd"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "segmento_comportamiento": "Segmento",
            "comercios": "# Comercios",
            "volumen": "Volumen Total",
            "margen": "Margen Total",
            "vol_share": "% del Volumen",
            "margen_pct": "Margen % Prom.",
            "estrategia": "Estrategia Comercial"
        }
    )

    st.markdown("---")

    # Distribución por tamaño
    st.markdown("#### 📏 Segmentación por Tamaño")

    tamaño_summary = comercios_activos.groupby("segmento_tamaño").agg(
        comercios=("rut_comercio", "count"),
        volumen=("monto_total_anual", "sum"),
        margen=("margen_estimado", "sum"),
        vol_promedio=("monto_total_anual", "mean"),
    ).reset_index()

    # Ordenar por orden lógico
    orden_tamaño = ["Estándar", "PRO", "PRO Max", "Enterprise", "Corporativo"]
    tamaño_summary["_orden"] = tamaño_summary["segmento_tamaño"].map(
        {t: i for i, t in enumerate(orden_tamaño)}
    )
    tamaño_summary = tamaño_summary.sort_values("_orden").drop("_orden", axis=1)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.dataframe(
            tamaño_summary.style.format({
                "volumen": format_currency,
                "margen": format_currency,
                "vol_promedio": format_currency,
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "segmento_tamaño": "Tamaño",
                "comercios": "# Comercios",
                "volumen": "Volumen Total",
                "margen": "Margen Total",
                "vol_promedio": "Vol. Promedio"
            }
        )

    with col2:
        st.bar_chart(
            tamaño_summary.set_index("segmento_tamaño")["comercios"],
            use_container_width=True
        )
        st.caption("Distribución de comercios por tamaño")

    st.markdown("---")

    # Matriz 2D
    st.markdown("#### 🎲 Matriz Estratégica 2D (Top 15 Combinaciones)")

    matriz_2d = comercios_activos.groupby(
        ["segmento_comportamiento", "segmento_tamaño"]
    ).agg(
        comercios=("rut_comercio", "count"),
        volumen=("monto_total_anual", "sum"),
        margen=("margen_estimado", "sum"),
        margen_pct=("margen_pct_volumen", "mean"),
    ).reset_index()

    # Calcular importancia estratégica
    matriz_2d["vol_share"] = matriz_2d["volumen"] / total_vol * 100
    matriz_2d = matriz_2d.sort_values("volumen", ascending=False).head(15)

    # Identificar segmentos estratégicos (top 80% del volumen)
    matriz_2d["vol_cumsum"] = matriz_2d["vol_share"].cumsum()
    matriz_2d["estratégico"] = matriz_2d["vol_cumsum"] <= 80

    st.dataframe(
        matriz_2d[[
            "segmento_comportamiento", "segmento_tamaño", "comercios",
            "volumen", "margen", "vol_share", "estratégico"
        ]].style.format({
            "volumen": format_currency,
            "margen": format_currency,
            "vol_share": "{:.1f}%",
        }).apply(
            lambda x: ["background-color: #d4edda" if v else "" for v in x],
            subset=["estratégico"]
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "segmento_comportamiento": "Comportamiento",
            "segmento_tamaño": "Tamaño",
            "comercios": "# Comercios",
            "volumen": "Volumen",
            "margen": "Margen",
            "vol_share": "% Vol.",
            "estratégico": "⭐ Estratégico"
        }
    )

    st.caption(
        "💡 **Segmentos estratégicos** (marcados en verde): Representan el 80% del volumen. "
        "Priorizar recursos comerciales en estos micro-segmentos maximiza el impacto."
    )


def render_advanced_visualizations(df: pd.DataFrame) -> None:
    """Renderiza visualizaciones avanzadas."""
    st.markdown("### 📈 Análisis Visual")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Margen vs Volumen")

        # Preparar datos para scatter
        plot_data = df[
            (df["monto_total_anual"] > 0) &
            (df["margen_pct_volumen"].notna())
        ].copy()

        # Limitar outliers para mejor visualización
        plot_data = plot_data[
            (plot_data["margen_pct_volumen"] > -0.02) &
            (plot_data["margen_pct_volumen"] < 0.05)
        ]

        if len(plot_data) > 0:
            # Usar scatter_chart de Streamlit
            chart_df = plot_data[["monto_total_anual", "margen_pct_volumen"]].copy()
            chart_df.columns = ["Volumen Anual", "Margen %"]
            st.scatter_chart(
                chart_df,
                x="Volumen Anual",
                y="Margen %",
                size=20,
                color="#1f77b4",
            )
            st.caption("Cada punto = un comercio. Outliers excluidos para claridad.")
        else:
            st.info("No hay datos suficientes para el gráfico")

    with col2:
        st.markdown("#### Distribución de Gap Competitivo")

        gap_data = df["gap_pricing_mdr"].dropna()
        if len(gap_data) > 0:
            # Crear histograma manual
            hist_data = pd.DataFrame({
                "Gap (bps)": (gap_data * 10000).clip(-50, 100)  # Convertir a bps y limitar
            })
            st.bar_chart(hist_data["Gap (bps)"].value_counts().sort_index())
            st.caption(
                "Distribución del gap competitivo en puntos base. "
                "Positivo = Klap más caro que Transbank."
            )
        else:
            st.info("No hay datos de gap competitivo")


def render_plan_recommendations(
    proposal_df: pd.DataFrame,
    scenario_df: pd.DataFrame
) -> None:
    """Renderiza recomendaciones de planes con justificación."""
    st.markdown("### 💼 Planes Recomendados")

    # Filtrar propuestas relevantes
    plan_cols = [
        "rut_comercio",
        "plan_recomendado",
        "plan_mdr_propuesto",
        "plan_fijo_propuesto",
        "addons_recomendados",
        "segmento_cluster_label",
        "segmento_promedio_volumen",
        "monto_total_anual",
        "margen_estimado",
        "gap_pricing_mdr",
    ]
    plan_cols = [col for col in plan_cols if col in proposal_df.columns]

    proposal_filtered = proposal_df.loc[
        proposal_df["rut_comercio"].isin(scenario_df["rut_comercio"]),
        plan_cols
    ].copy()

    # Agregar justificación
    if len(proposal_filtered) > 0 and "gap_pricing_mdr" in proposal_filtered.columns:
        def generate_justification(row):
            justif = []

            # Basado en volumen
            volume = row.get("monto_total_anual", 0)
            if volume > 50_000_000:
                justif.append("Alto volumen")
            elif volume > 10_000_000:
                justif.append("Volumen medio")

            # Basado en gap competitivo
            gap = row.get("gap_pricing_mdr", 0)
            if gap > 0.0015:
                justif.append("brecha competitiva alta")
            elif gap > 0.0005:
                justif.append("brecha competitiva moderada")

            # Basado en margen
            margin = row.get("margen_estimado", 0)
            if margin < 0:
                justif.append("margen negativo")

            return " | ".join(justif) if justif else "Perfil estándar"

        proposal_filtered["Justificación"] = proposal_filtered.apply(
            generate_justification, axis=1
        )

    # Mostrar tabla
    display_cols = [c for c in proposal_filtered.columns if c != "rut_comercio"]
    st.dataframe(
        proposal_filtered[display_cols].sort_values(
            "monto_total_anual", ascending=False
        ) if "monto_total_anual" in display_cols else proposal_filtered[display_cols],
        use_container_width=True,
        hide_index=True,
    )

    # Botón de descarga
    st.download_button(
        "📥 Descargar plan recomendado (CSV)",
        proposal_filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"planes_recomendados_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


def render_simulator(
    df: pd.DataFrame,
    clusters: List[str],
    segment_column: str = "segmento_cluster_label",
) -> Tuple[pd.DataFrame, bool]:
    """
    Renderiza simulador mejorado con escenarios preconfigurados.
    Retorna (scenario_df, simulation_active).

    Args:
        df: DataFrame con datos de comercios
        clusters: Lista de clusters/segmentos disponibles
        segment_column: Columna a usar para identificar segmentos
    """
    st.markdown("### 🎮 Simulador de Escenarios")

    st.markdown(
        "Simula el impacto de ajustes en tarifas (MDR y fijo) sobre márgenes y volumen. "
        "Puedes usar escenarios preconfigurados o crear uno personalizado."
    )

    # Tabs para tipo de simulación
    tab1, tab2 = st.tabs(["📋 Escenarios Preconfigurados", "⚙️ Personalizado"])

    sim_enabled = False
    sim_targets = []
    sim_mdr_delta = 0.0
    sim_fijo_delta = 0.0

    with tab1:
        st.markdown("Selecciona un escenario predefinido:")

        scenario_cols = st.columns(2)
        selected_preset = None

        for idx, (key, scenario) in enumerate(PRESET_SCENARIOS.items()):
            col = scenario_cols[idx % 2]
            with col:
                if st.button(
                    f"**{scenario['name']}**\n\n{scenario['description']}",
                    key=f"preset_{key}",
                    use_container_width=True,
                ):
                    selected_preset = scenario

        if selected_preset:
            st.success(f"✅ Escenario seleccionado: {selected_preset['name']}")
            sim_enabled = True
            sim_targets = st.multiselect(
                "Clusters afectados",
                options=clusters,
                default=clusters,
            )
            sim_mdr_delta = selected_preset["mdr_delta"]
            sim_fijo_delta = selected_preset["fijo_delta"]

            st.info(
                f"Δ MDR: {sim_mdr_delta:+.2f} pp | "
                f"Δ Fijo: {sim_fijo_delta:+.0f} CLP"
            )

    with tab2:
        sim_enabled_custom = st.checkbox("Activar simulación personalizada")

        if sim_enabled_custom:
            sim_enabled = True
            sim_targets = st.multiselect(
                "Segmentos afectados",
                options=clusters,
                default=clusters,
            )

            col1, col2 = st.columns(2)
            with col1:
                sim_mdr_delta = st.slider(
                    "Δ MDR (puntos porcentuales)",
                    -1.00,
                    1.00,
                    0.00,
                    0.05,
                )
            with col2:
                sim_fijo_delta = st.slider(
                    "Δ fijo (CLP por transacción)",
                    -150.0,
                    150.0,
                    0.0,
                    5.0,
                )

    # Aplicar simulación
    if sim_enabled and sim_targets:
        scenario_df = apply_simulation(
            df,
            sim_targets,
            sim_mdr_delta,
            sim_fijo_delta,
            segment_column=segment_column,
        )

        # Mostrar impacto estimado
        st.markdown("---")
        st.markdown("#### 📊 Impacto Estimado")

        impacted = scenario_df[scenario_df[segment_column].isin(sim_targets)]

        margen_actual = impacted["margen_estimado"].sum()
        margen_simulado = impacted["margen_estimado_sim"].sum()
        delta_margen = margen_simulado - margen_actual

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Comercios afectados",
            f"{len(impacted):,}",
        )
        col2.metric(
            "Margen actual",
            format_currency(margen_actual),
        )
        col3.metric(
            "Margen simulado",
            format_currency(margen_simulado),
            delta=format_currency(delta_margen),
        )

        return scenario_df, True
    else:
        # Sin simulación: copiar valores actuales
        scenario_df = df.copy()
        scenario_df["klap_mdr_sim"] = scenario_df["klap_mdr"]
        scenario_df["klap_fijo_sim"] = scenario_df["klap_fijo_clp"]
        scenario_df["margen_estimado_sim"] = scenario_df["margen_estimado"]
        scenario_df["margen_pct_volumen_sim"] = scenario_df["margen_pct_volumen"]

        return scenario_df, False


# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================


def main() -> None:
    """Función principal de la aplicación."""

    # Configuración de página
    st.set_page_config(
        page_title="Modelo de Pricing Klap",
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Header
    st.title("💳 Modelo de Pricing Klap")
    st.markdown(
        "Dashboard estratégico para análisis de pricing, segmentación de comercios "
        "y simulación de escenarios comerciales."
    )
    st.markdown("---")

    # ========================================================================
    # SIDEBAR: Carga de datos y filtros
    # ========================================================================

    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("### 📁 Datos de entrada")

    uploaded_model = st.sidebar.file_uploader(
        "Resultados del modelo",
        type=["parquet"],
        key="upload_model",
        help="merchant_pricing_model_results.parquet"
    )
    uploaded_feature = st.sidebar.file_uploader(
        "Base de features",
        type=["parquet"],
        key="upload_feature",
        help="merchant_pricing_feature_base.parquet"
    )
    uploaded_proposals = st.sidebar.file_uploader(
        "Propuestas comerciales",
        type=["parquet"],
        key="upload_proposals",
        help="merchant_pricing_proposals.parquet"
    )

    # ========================================================================
    # Carga y validación de datos
    # ========================================================================

    try:
        with st.spinner("🔄 Cargando datos..."):
            # Cargar archivos
            model_df, feature_df, proposal_df, data_source = load_sources(
                uploaded_model,
                uploaded_feature,
                uploaded_proposals,
                DEFAULT_MODEL_FILE,
                DEFAULT_FEATURE_FILE,
                DEFAULT_PROPOSALS_FILE,
            )

            # Cargar precios de referencia (SIN FALLBACK)
            pricing_reference = load_pricing_reference()

            # Calcular tarifas efectivas
            pricing_rates = compute_effective_rates(
                pricing_reference,
                assumed_mix=ASSUMED_MIX_DEFAULT,
                fallback_segments=FALLBACK_SEGMENTS_DEFAULT,
            )

            # Actualizar métricas de pricing
            model_df = refresh_pricing_metrics(model_df, pricing_rates)

            # Copias para trabajo
            feature_df = feature_df.copy()
            proposal_df = proposal_df.copy()

        st.sidebar.success(f"✅ Datos cargados: {data_source}")
        
        # Mostrar timestamp de última actualización de archivos
        if DEFAULT_MODEL_FILE.exists():
            from datetime import datetime
            mod_time = datetime.fromtimestamp(DEFAULT_MODEL_FILE.stat().st_mtime)
            st.sidebar.caption(
                f"📅 Archivos generados: {mod_time.strftime('%Y-%m-%d %H:%M')}"
            )

        # Validar propuestas
        if {"plan_mdr_propuesto", "plan_fijo_propuesto"}.issubset(proposal_df.columns):
            propuestas_sin_tarifa = (
                proposal_df["plan_mdr_propuesto"].abs().sum() < 1e-12
                and proposal_df["plan_fijo_propuesto"].abs().sum() < 1e-6
            )
            if propuestas_sin_tarifa:
                st.sidebar.warning(
                    "⚠️ Las propuestas no incluyen MDR/fijo. "
                    "Regenera el archivo de propuestas."
                )

    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"❌ Error inesperado al cargar datos:\n{exc}")
        st.stop()

    # ========================================================================
    # Preparar opciones de filtros
    # ========================================================================

    # Verificar si existe segmentación mejorada
    tiene_segmentacion_mejorada = all(
        col in model_df.columns
        for col in ["segmento_comportamiento", "segmento_tamaño"]
    )

    # Opciones de filtros (adaptar según segmentación disponible)
    if tiene_segmentacion_mejorada:
        comportamientos = sorted(
            model_df["segmento_comportamiento"].dropna().unique()
        )
        tamaños = sorted(
            model_df["segmento_tamaño"].dropna().unique(),
            key=lambda x: ["Estándar", "PRO", "PRO Max", "Enterprise", "Corporativo"].index(x)
            if x in ["Estándar", "PRO", "PRO Max", "Enterprise", "Corporativo"] else 99
        )
    else:
        # Fallback a segmentación original
        comportamientos = sorted(model_df["segmento_cluster_label"].dropna().unique())
        tamaños = sorted(
            model_df["segmento_promedio_volumen"].dropna().astype(str).unique()
        )

    acciones = sorted(model_df["accion_sugerida"].dropna().unique())

    # ========================================================================
    # SIDEBAR: Filtros
    # ========================================================================

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filtros de Segmentación")

    if tiene_segmentacion_mejorada:
        st.sidebar.caption(
            "✨ **Nueva segmentación 2D activa**\n\n"
            "Filtra comercios por comportamiento y tamaño para análisis más granular."
        )

        comportamiento_filter = st.sidebar.multiselect(
            "🎯 Comportamiento del Comercio",
            options=comportamientos,
            default=comportamientos,
            help=(
                "Tipo de comportamiento basado en volumen, margen, actividad y brecha competitiva.\n\n"
                "Ejemplos:\n"
                "• Champions: Alto volumen + alto margen\n"
                "• Potencial Alto: Alto volumen + margen mejorable\n"
                "• En Riesgo: Margen negativo o brecha competitiva alta"
            )
        )

        tamaño_filter = st.sidebar.multiselect(
            "📏 Tamaño por Volumen",
            options=tamaños,
            default=tamaños,
            help=(
                "Segmento según volumen transaccional mensual.\n\n"
                "• Estándar: <$5MM/mes\n"
                "• PRO: $5MM-$15MM/mes\n"
                "• PRO Max: $15MM-$40MM/mes\n"
                "• Enterprise: $40MM-$100MM/mes\n"
                "• Corporativo: >$100MM/mes"
            )
        )

        # Filtro adicional de acción sugerida
        accion_filter = st.sidebar.multiselect(
            "⚡ Acción Recomendada",
            options=acciones,
            default=acciones,
            help="Acción comercial sugerida por el modelo de pricing"
        )

        # Aplicar filtros con segmentación mejorada
        filtered = model_df[
            model_df["segmento_comportamiento"].isin(comportamiento_filter)
            & model_df["segmento_tamaño"].isin(tamaño_filter)
            & model_df["accion_sugerida"].isin(accion_filter)
        ].copy()

    else:
        st.sidebar.caption(
            "📊 **Segmentación básica**\n\n"
            "Para habilitar la segmentación 2D mejorada, ejecuta el notebook completo."
        )

        cluster_filter = st.sidebar.multiselect(
            "Segmento de Cluster",
            options=comportamientos,
            default=comportamientos,
            help="Segmentos generados por clustering"
        )

        segmento_filter = st.sidebar.multiselect(
            "Plan Comercial",
            options=tamaños,
            default=tamaños,
            help="Plan comercial actual del comercio"
        )

        accion_filter = st.sidebar.multiselect(
            "Acción Sugerida",
            options=acciones,
            default=acciones,
            help="Acción recomendada según reglas de negocio"
        )

        # Aplicar filtros con segmentación original
        filtered = model_df[
            model_df["segmento_cluster_label"].isin(cluster_filter)
            & model_df["accion_sugerida"].isin(accion_filter)
            & model_df["segmento_promedio_volumen"].astype(str).isin(segmento_filter)
        ].copy()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"📊 Mostrando {len(filtered):,} de {len(model_df):,} comercios"
    )

    # ========================================================================
    # Información temporal
    # ========================================================================

    period_info = compute_period_info(model_df)

    # ========================================================================
    # TABS PRINCIPALES
    # ========================================================================

    # Determinar número de tabs según segmentación disponible
    if tiene_segmentacion_mejorada:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard Ejecutivo",
            "🗺️ Mapa de Segmentación",
            "🎯 Análisis Detallado",
            "🎮 Simulador",
            "📋 Datos Completos"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard Ejecutivo",
            "🎯 Análisis Detallado",
            "🎮 Simulador",
            "📋 Datos Completos"
        ])

    # ========================================================================
    # TAB 1: Dashboard Ejecutivo
    # ========================================================================

    with tab1:
        render_executive_dashboard(filtered, period_info)
        render_action_prioritization(filtered)
        render_advanced_visualizations(filtered)

    # ========================================================================
    # TAB 2: Mapa de Segmentación (solo si está disponible)
    # ========================================================================

    if tiene_segmentacion_mejorada:
        with tab2:
            st.markdown("## 🗺️ Mapa Estratégico de Segmentación")
            render_segmentation_map(filtered)

    # ========================================================================
    # TAB 3 (o 2 si no hay segmentación mejorada): Análisis Detallado
    # ========================================================================

    with (tab3 if tiene_segmentacion_mejorada else tab2):
        st.markdown("## 🎯 Análisis Detallado")

        # Planes recomendados
        render_plan_recommendations(proposal_df, filtered)

        st.markdown("---")

        # Distribución por acción
        st.markdown("### 📊 Distribución por Acción Sugerida")
        action_summary = (
            filtered.groupby("accion_sugerida")
            .agg(
                comercios=("rut_comercio", "count"),
                volumen=("monto_total_anual", "sum"),
                margen=("margen_estimado", "sum"),
            )
            .sort_values("volumen", ascending=False)
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(
                action_summary.style.format({
                    "volumen": format_currency,
                    "margen": format_currency,
                }),
                use_container_width=True,
            )
        with col2:
            st.bar_chart(action_summary["volumen"])

        st.markdown("---")

        # Resumen por cluster
        st.markdown("### 🏷️ Resumen por Cluster Analítico")
        cluster_summary = (
            filtered.groupby("segmento_cluster_label")
            .agg(
                comercios=("rut_comercio", "count"),
                volumen=("monto_total_anual", "sum"),
                margen=("margen_estimado", "sum"),
                margen_pct=("margen_pct_volumen", "mean"),
                gap_promedio=("gap_pricing_mdr", "mean"),
            )
            .sort_values("volumen", ascending=False)
        )
        st.dataframe(
            cluster_summary.style.format({
                "volumen": format_currency,
                "margen": format_currency,
                "margen_pct": "{:.2%}",
                "gap_promedio": lambda x: format_basis_points(x),
            }),
            use_container_width=True,
        )

    # ========================================================================
    # TAB 4 (o 3 si no hay segmentación mejorada): Simulador
    # ========================================================================

    with (tab4 if tiene_segmentacion_mejorada else tab3):
        st.markdown("## 🎮 Simulador de Escenarios")

        # Determinar qué columna usar para clusters en simulador
        if tiene_segmentacion_mejorada:
            clusters_for_sim = sorted(model_df["segmento_comportamiento"].dropna().unique())
            segment_col = "segmento_comportamiento"
        else:
            clusters_for_sim = sorted(model_df["segmento_cluster_label"].dropna().unique())
            segment_col = "segmento_cluster_label"

        scenario_df, sim_active = render_simulator(
            filtered,
            clusters_for_sim,
            segment_column=segment_col
        )

        if sim_active:
            st.markdown("---")
            st.markdown("### 📊 Comparación: Actual vs Simulado")

            # Métricas comparativas
            col1, col2, col3 = st.columns(3)

            total_volume = scenario_df["monto_total_anual"].sum()
            margin_actual = scenario_df["margen_estimado"].sum()
            margin_sim = scenario_df["margen_estimado_sim"].sum()

            col1.metric("Volumen total", format_currency(total_volume))
            col2.metric(
                "Margen actual",
                format_currency(margin_actual),
                help="Margen con tarifas actuales"
            )
            col3.metric(
                "Margen simulado",
                format_currency(margin_sim),
                delta=format_currency(margin_sim - margin_actual),
                help="Margen con tarifas ajustadas"
            )

            # Tabla comparativa top comercios
            st.markdown("#### Top 20 Comercios Más Impactados")

            comparison = scenario_df.copy()
            comparison["delta_margen"] = (
                comparison["margen_estimado_sim"] - comparison["margen_estimado"]
            )
            comparison["delta_margen_pct"] = (
                comparison["margen_pct_volumen_sim"] - comparison["margen_pct_volumen"]
            )

            top_impacted = comparison.nlargest(20, "delta_margen", keep="first")

            display_cols = [
                "rut_comercio",
                "segmento_cluster_label",
                "monto_total_anual",
                "margen_estimado",
                "margen_estimado_sim",
                "delta_margen",
                "margen_pct_volumen",
                "margen_pct_volumen_sim",
            ]
            display_cols = [c for c in display_cols if c in top_impacted.columns]

            st.dataframe(
                top_impacted[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("👆 Activa una simulación arriba para ver el análisis comparativo")

    # ========================================================================
    # TAB 5 (o 4 si no hay segmentación mejorada): Datos Completos
    # ========================================================================

    with (tab5 if tiene_segmentacion_mejorada else tab4):
        st.markdown("## 📋 Datos Completos")

        # Detalle por comercio
        st.markdown("### 🏢 Detalle por Comercio")

        detail_cols = [
            "rut_comercio",
            "segmento_cluster_label",
            "segmento_promedio_volumen",
            "accion_sugerida",
            "monto_total_anual",
            "margen_estimado",
            "margen_pct_volumen",
            "gap_pricing_mdr",
            "klap_mdr",
            "competidor_mdr",
            "n_terminales_max",
            "n_tecnologias_unicas",
            "share_meses_activos",
        ]
        detail_cols = [c for c in detail_cols if c in filtered.columns]

        st.dataframe(
            filtered[detail_cols].sort_values("monto_total_anual", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "📥 Descargar datos filtrados (CSV)",
            filtered[detail_cols].to_csv(index=False).encode("utf-8"),
            file_name=f"pricing_detalle_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        st.markdown("---")

        # Mix de marcas
        st.markdown("### 💳 Mix de Marcas (Visa/Mastercard)")

        mix_cols = ["rut_comercio", "share_visa", "share_mastercard"]
        mix_cols = [c for c in mix_cols if c in model_df.columns]

        if len(mix_cols) == 3:
            mix_df = (
                model_df.loc[
                    model_df["rut_comercio"].isin(filtered["rut_comercio"]),
                    mix_cols
                ]
                .set_index("rut_comercio")
                .clip(0, 1)
            )
            st.dataframe(
                mix_df.style.format("{:.1%}"),
                use_container_width=True,
            )

            st.caption(
                "💡 El mix de marcas afecta directamente el costo de interchange. "
                "Un mayor share de débito/Mastercard típicamente reduce costos."
            )
        else:
            st.info("No se encontraron columnas de mix de marcas en los datos.")

    # ========================================================================
    # FOOTER: Notas y documentación
    # ========================================================================

    st.markdown("---")

    with st.expander("📖 Notas y Definiciones"):
        st.markdown("""
        ### Métricas Clave

        - **Margen estimado**: Ingresos (MDR + comisión fija) menos costos mínimos (interchange + marca)
          - **IMPORTANTE**: Los costos de marca incluyen ajuste histórico de 70% 
            (archivo `costos_marca_25_1.xlsx` contiene proyecciones 2025, 
            pero datos transaccionales son 2024)
        - **Margen % volumen**: Margen estimado dividido por volumen transaccional
        - **Gap pricing MDR**: Diferencia entre MDR de Klap y benchmark Transbank
          - Positivo: Klap más caro que competencia
          - Negativo: Klap más barato que competencia
        - **Score de prioridad**: Métrica compuesta (0-100) que considera:
          - Volumen del comercio (impacto potencial)
          - Urgencia del margen (rentabilidad)
          - Brecha competitiva (riesgo de churn)
        
        ### Comercios con Margen Negativo
        
        Si existen comercios con margen negativo después del ajuste histórico de costos,
        las causas probables son:
        
        1. **Tarifas especiales**: Descuentos negociados no reflejados en grilla oficial
        2. **Mix de tarjetas atípico**: Alto porcentaje de débito (intercambio ~0.50%)
        3. **Genuinamente no rentables**: Requieren renegociación o revisión de contrato
        
        Estos comercios aparecen con la acción "Ajustar MDR urgente" y requieren 
        validación de tarifas reales contra la base transaccional

        ### Clusters Analíticos

        Los clusters se generan mediante análisis de comportamiento y no corresponden
        necesariamente a los planes comerciales (Estándar, PRO, PRO Max).

        Ejemplos típicos:
        - **Alto valor**: Comercios grandes con buen margen
        - **Brecha competitiva**: Comercios donde Klap es más caro
        - **Oportunidad de crecimiento**: Comercios con potencial no explotado

        ### Simulaciones

        El simulador permite evaluar el impacto de ajustes de tarifas antes de
        implementarlos. Los escenarios preconfigurados reflejan estrategias típicas:

        - **Conservador**: Ajuste mínimo para competitividad
        - **Igualar Transbank**: Equiparar tarifas al líder de mercado
        - **Agresivo**: Captura de mercado mediante precio
        - **Incremento Premium**: Monetización de segmentos de alto valor

        ### Fuentes de Datos y Limitaciones

        - **Precios oficiales**: `data/precios_actuales_klap.xlsx` (fuente única de verdad)
        - **Costos de marca**: `costos_marca_25_1.xlsx` con factor de ajuste histórico 0.70
        - **Datos transaccionales**: Procesados mediante notebook `main_pricingklap.ipynb`
        - **Benchmark competencia**: Datos públicos de Transbank
        
        **Limitaciones conocidas**:
        - Mix de tarjetas asumido globalmente (60% crédito, 35% débito, 5% prepago)
        - Costos de marca ajustados con factor histórico conservador
        - No incluye costos operacionales directos ni overhead
        - Competencia limitada a Transbank (falta incorporar Getnet, Redelcom)

        ---

        **Versión**: 2.1 | **Actualización**: 2025-11-17
        
        **Cambios recientes**:
        - Ajuste histórico de costos de marca 2024 (factor 0.70)
        - Validación mejorada de márgenes negativos
        - Documentación de limitaciones y supuestos

        Para soporte o reportar problemas: contactar al equipo de Analytics.
        """)

    st.caption(
        "💳 Modelo de Pricing Klap | Datos confidenciales - Uso interno exclusivo"
    )


if __name__ == "__main__":
    main()
