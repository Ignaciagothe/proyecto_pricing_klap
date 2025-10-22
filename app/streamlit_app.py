import math
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BASE_DIR / "data" / "processed"
DEFAULT_MODEL_FILE = DEFAULT_DATA_DIR / "merchant_pricing_model_results.parquet"
DEFAULT_FEATURE_FILE = DEFAULT_DATA_DIR / "merchant_pricing_feature_base.parquet"
DEFAULT_PROPOSALS_FILE = DEFAULT_DATA_DIR / "merchant_pricing_proposals.parquet"


@st.cache_data(show_spinner=False)
def load_local_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {path}")
    return pd.read_parquet(path)


def load_sources(
    uploaded_model,
    uploaded_feature,
    uploaded_proposals,
    default_model: Path,
    default_feature: Path,
    default_proposals: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Carga datos desde archivos subidos o rutas por defecto."""
    if uploaded_model is not None:
        model_df = pd.read_parquet(uploaded_model)
        source = "Archivos cargados manualmente"
    elif default_model.exists():
        model_df = load_local_parquet(default_model)
        source = f"Ruta local: {default_model}"
    else:
        raise FileNotFoundError(
            "No se encontró `merchant_pricing_model_results.parquet`. "
            "Sube un archivo para continuar."
        )

    if uploaded_feature is not None:
        feature_df = pd.read_parquet(uploaded_feature)
    elif default_feature.exists():
        feature_df = load_local_parquet(default_feature)
    else:
        raise FileNotFoundError(
            "No se encontró `merchant_pricing_feature_base.parquet`. "
            "Sube un archivo para continuar."
        )

    if uploaded_proposals is not None:
        proposal_df = pd.read_parquet(uploaded_proposals)
    elif default_proposals.exists():
        proposal_df = load_local_parquet(default_proposals)
    else:
        # si no existe propuesta, usamos merchant_pricing_base y planes sin asignar
        proposal_df = model_df.copy()

    return model_df, feature_df, proposal_df, source


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "—"
    if abs(value) >= 1e9:
        return f"${value/1e9:,.2f}B"
    if abs(value) >= 1e6:
        return f"${value/1e6:,.2f}MM"
    return f"${value:,.0f}"


def format_percent(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value*100:.2f}%"


def main() -> None:
    st.set_page_config(
        page_title="Modelo de Pricing Klap",
        page_icon="💳",
        layout="wide",
    )
    st.title("Modelo de Pricing Klap")
    st.caption(
        "Explora márgenes, brechas competitivas y segmentación de comercios. "
        "Puedes subir archivos Parquet generados por el notebook o utilizar los que estén en `data/processed/`."
    )

    st.sidebar.header("Datos de entrada")
    uploaded_model = st.sidebar.file_uploader(
        "Resultados del modelo (`merchant_pricing_model_results.parquet`)",
        type=["parquet"],
        key="upload_model",
    )
    uploaded_feature = st.sidebar.file_uploader(
        "Base de features (`merchant_pricing_feature_base.parquet`)",
        type=["parquet"],
        key="upload_feature",
    )
    uploaded_proposals = st.sidebar.file_uploader(
        "Propuestas comerciales (`merchant_pricing_proposals.parquet`)",
        type=["parquet"],
        key="upload_proposals",
    )

    try:
        with st.spinner("Cargando datos..."):
            model_df, feature_df, proposal_df, data_source = load_sources(
                uploaded_model,
                uploaded_feature,
                uploaded_proposals,
                DEFAULT_MODEL_FILE,
                DEFAULT_FEATURE_FILE,
                DEFAULT_PROPOSALS_FILE,
            )
        st.success(f"Datos cargados desde: {data_source}")
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    required_cols = {
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
    }
    missing_cols = required_cols - set(model_df.columns)
    if missing_cols:
        st.error(
            "Faltan columnas en el archivo de resultados del modelo: "
            + ", ".join(sorted(missing_cols))
        )
        st.stop()

    proposal_required = {"plan_recomendado", "addons_recomendados", "plan_mdr_propuesto", "plan_fijo_propuesto"}
    missing_proposal_cols = proposal_required - set(proposal_df.columns)
    if missing_proposal_cols:
        st.warning(
            "El archivo de propuestas no contiene todas las columnas esperadas "
            f"({', '.join(sorted(missing_proposal_cols))}). Se generarán recomendaciones básicas."
        )
        proposal_df = model_df.copy()
        for col in proposal_required:
            if col not in proposal_df.columns:
                proposal_df[col] = "Sin información"

    clusters = sorted(model_df["segmento_cluster_label"].dropna().unique())
    acciones = sorted(model_df["accion_sugerida"].dropna().unique())
    volumen_segmentos = (
        model_df["segmento_promedio_volumen"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    st.sidebar.header("Filtros")
    cluster_filter = st.sidebar.multiselect(
        "Segmento cluster",
        options=clusters,
        default=clusters,
    )
    accion_filter = st.sidebar.multiselect(
        "Acción sugerida",
        options=acciones,
        default=acciones,
    )
    segmento_filter = st.sidebar.multiselect(
        "Segmento volumen (Klap)",
        options=volumen_segmentos,
        default=volumen_segmentos,
    )
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Ajusta los filtros para analizar campañas específicas (por ejemplo, comercios en "
        "Brecha competitiva con recomendación de ajuste urgente)."
    )

    filtered = model_df[
        model_df["segmento_cluster_label"].isin(cluster_filter)
        & model_df["accion_sugerida"].isin(accion_filter)
        & model_df["segmento_promedio_volumen"].astype(str).isin(segmento_filter)
    ].copy()

    st.sidebar.header("Simulación de ajustes")
    sim_enabled = st.sidebar.checkbox("Activar simulación sobre la selección")
    sim_targets = st.sidebar.multiselect(
        "Segmentos afectados",
        options=clusters,
        default=clusters,
        disabled=not sim_enabled,
    )
    sim_mdr_delta = st.sidebar.slider(
        "Δ MDR (puntos porcentuales)", -1.00, 1.00, 0.00, 0.05, disabled=not sim_enabled
    )
    sim_fijo_delta = st.sidebar.slider(
        "Δ fijo (CLP por transacción)", -150.0, 150.0, 0.0, 5.0, disabled=not sim_enabled
    )

    scenario_df = filtered.copy()
    if sim_enabled and sim_targets:
        mask = scenario_df["segmento_cluster_label"].isin(sim_targets)
        scenario_df.loc[mask, "klap_mdr_sim"] = scenario_df.loc[mask, "klap_mdr"] + (
            sim_mdr_delta / 100
        )
        scenario_df.loc[mask, "klap_fijo_sim"] = scenario_df.loc[mask, "klap_fijo_clp"] + sim_fijo_delta
        # En caso de que falte la columna de fijo original, generamos una serie en cero
        if "klap_fijo_clp" not in scenario_df.columns:
            scenario_df["klap_fijo_clp"] = 0.0
            scenario_df["klap_fijo_sim"] = sim_fijo_delta
        scenario_df["klap_mdr_sim"] = scenario_df["klap_mdr_sim"].fillna(scenario_df["klap_mdr"])
        scenario_df["klap_fijo_sim"] = scenario_df["klap_fijo_sim"].fillna(scenario_df["klap_fijo_clp"])

        scenario_df["ingreso_variable_sim"] = (
            scenario_df["monto_total_anual"] * scenario_df["klap_mdr_sim"]
        )
        qtrx_total = scenario_df.get("qtrx_total_anual", 0.0)
        scenario_df["ingreso_fijo_sim"] = qtrx_total * scenario_df["klap_fijo_sim"]
        scenario_df["ingreso_total_sim"] = (
            scenario_df["ingreso_variable_sim"] + scenario_df.get("ingreso_fijo_sim", 0.0)
        )
        scenario_df["margen_estimado_sim"] = scenario_df["ingreso_total_sim"] - scenario_df["costo_min_estimado"]
        scenario_df["margen_pct_volumen_sim"] = np.where(
            scenario_df["monto_total_anual"] > 0,
            scenario_df["margen_estimado_sim"] / scenario_df["monto_total_anual"],
            np.nan,
        )
    else:
        scenario_df["klap_mdr_sim"] = scenario_df["klap_mdr"]
        scenario_df["klap_fijo_sim"] = scenario_df.get("klap_fijo_clp", 0.0)
        scenario_df["margen_estimado_sim"] = scenario_df["margen_estimado"]
        scenario_df["margen_pct_volumen_sim"] = scenario_df["margen_pct_volumen"]

    total_volume = scenario_df["monto_total_anual"].sum()
    total_margin = scenario_df["margen_estimado_sim"].sum()
    avg_margin_pct = scenario_df["margen_pct_volumen_sim"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Volumen anual (CLP)", format_currency(total_volume))
    col2.metric(
        "Margen estimado (CLP)",
        format_currency(total_margin),
        delta=format_currency(total_margin - filtered["margen_estimado"].sum())
        if sim_enabled and sim_targets
        else None,
    )
    col3.metric(
        "Margen % promedio",
        format_percent(avg_margin_pct),
        delta=format_percent(avg_margin_pct - filtered["margen_pct_volumen"].mean())
        if sim_enabled and sim_targets
        else None,
    )

    st.subheader("Planes recomendados")
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
    ]
    plan_cols = [col for col in plan_cols if col in proposal_df.columns]
    proposal_filtered = proposal_df.loc[
        proposal_df["rut_comercio"].isin(scenario_df["rut_comercio"]), plan_cols
    ].copy()
    st.dataframe(
        proposal_filtered.sort_values("monto_total_anual", ascending=False),
        use_container_width=True,
    )

    st.download_button(
        "Descargar plan recomendado (CSV)",
        proposal_filtered.to_csv(index=False).encode("utf-8"),
        file_name="planes_recomendados.csv",
        mime="text/csv",
    )

    st.subheader("Distribución por acción sugerida")
    action_summary = (
        scenario_df.groupby("accion_sugerida")
        .agg(
            comercios=("rut_comercio", "count"),
            volumen=("monto_total_anual", "sum"),
            margen=("margen_estimado_sim", "sum"),
        )
        .sort_values("volumen", ascending=False)
    )
    st.dataframe(
        action_summary.style.format(
            {
                "volumen": format_currency,
                "margen": format_currency,
            }
        ),
        use_container_width=True,
    )
    st.bar_chart(action_summary["volumen"])

    st.subheader("Resumen por cluster")
    cluster_summary = (
        scenario_df.groupby("segmento_cluster_label")
        .agg(
            comercios=("rut_comercio", "count"),
            volumen=("monto_total_anual", "sum"),
            margen=("margen_estimado_sim", "sum"),
            margen_pct=("margen_pct_volumen_sim", "mean"),
        )
        .sort_values("volumen", ascending=False)
    )
    st.dataframe(
        cluster_summary.style.format(
            {"volumen": format_currency, "margen": format_currency, "margen_pct": "{:.2%}"}
        ),
        use_container_width=True,
    )

    st.subheader("Detalle por comercio")
    detail_cols = [
        "rut_comercio",
        "segmento_cluster_label",
        "segmento_promedio_volumen",
        "accion_sugerida",
        "monto_total_anual",
        "margen_estimado",
        "margen_estimado_sim",
        "margen_pct_volumen",
        "margen_pct_volumen_sim",
        "gap_pricing_mdr",
        "klap_mdr",
        "klap_mdr_sim",
        "competidor_mdr",
        "n_terminales_max",
        "n_tecnologias_unicas",
        "share_meses_activos",
    ]
    detail_cols = [c for c in detail_cols if c in scenario_df.columns]
    st.dataframe(
        scenario_df[detail_cols].sort_values("monto_total_anual", ascending=False),
        use_container_width=True,
    )

    st.download_button(
        "Descargar datos filtrados (CSV)",
        scenario_df[detail_cols].to_csv(index=False).encode("utf-8"),
        file_name="pricing_filtrado.csv",
        mime="text/csv",
    )

    st.subheader("Mix de marcas (Visa/Mastercard)")
    mix_cols = ["rut_comercio", "share_visa", "share_mastercard"]
    mix_cols = [c for c in mix_cols if c in model_df.columns]
    if len(mix_cols) == 3:
        mix_df = (
            model_df.loc[model_df["rut_comercio"].isin(scenario_df["rut_comercio"]), mix_cols]
            .set_index("rut_comercio")
            .clip(0, 1)
        )
        st.dataframe(
            mix_df.style.format("{:.1%}"),
            use_container_width=True,
        )
    else:
        st.info("No se encontraron columnas de mix de marcas para mostrar.")

    st.subheader("Indicadores adicionales del feature base")
    feature_subset = feature_df[feature_df["rut_comercio"].isin(scenario_df["rut_comercio"])]
    if "estado_terminal_actual" in feature_subset.columns:
        estado_counts = (
            feature_subset["estado_terminal_actual"]
            .value_counts()
            .rename_axis("estado_terminal_actual")
            .to_frame("comercios")
        )
        st.write("Estado actual de terminales (comercios seleccionados):")
        st.dataframe(estado_counts, use_container_width=True)

    if "n_tecnologias_unicas" in feature_subset.columns:
        st.write(
            f"Tecnologías distintas por comercio (promedio): "
            f"{feature_subset['n_tecnologias_unicas'].mean():.2f}"
        )

    if "meses_con_ventas" in feature_subset.columns and "meses_reportados" in feature_subset.columns:
        feature_subset["share_activos"] = np.where(
            feature_subset["meses_reportados"] > 0,
            feature_subset["meses_con_ventas"] / feature_subset["meses_reportados"],
            np.nan,
        )
        st.write(
            f"Participación promedio de meses activos: "
            f"{feature_subset['share_activos'].mean():.2%}"
        )

    st.subheader("Notas")
    st.markdown(
        """
        - `margen_estimado` = ingresos (MDR + fijo) − costos mínimos (interchange + marca).
        - `gap_pricing_mdr` positivo indica que la tarifa de Klap supera el benchmark Transbank.
        - Activa la simulación para evaluar ajustes de MDR/fijo por cluster antes de implementar cambios comerciales.
        - Sube nuevos Parquet cuando ejecutes nuevamente el notebook para actualizar resultados.
        """
    )
    st.caption("Fuente: modelo de pricing 2024. Todos los montos en CLP.")

    st.sidebar.header("Reporte ejecutivo")
    report_sections: List[str] = [
        f"- Comercios analizados: {len(filtered):,}",
        f"- Volumen total (selección): {format_currency(total_volume)}",
        f"- Margen estimado (selección): {format_currency(total_margin)}",
        "- Clusters incluidos: " + ", ".join(cluster_filter),
        "- Planes destacados: " + ", ".join(
            sorted(proposal_filtered["plan_recomendado"].dropna().unique())
        ),
        "- Add-ons sugeridos disponibles: " + ", ".join(
            sorted(
                {
                    addon.strip()
                    for addons_str in proposal_filtered["addons_recomendados"].dropna()
                    for addon in addons_str.split(",") if addon
                }
            )
        ),
    ]
    st.sidebar.download_button(
        "Descargar reporte ejecutivo",
        "\n".join(report_sections).encode("utf-8"),
        file_name="reporte_pricing.txt",
        mime="text/plain",
    )


if __name__ == "__main__":
    main()
