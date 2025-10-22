import math
from pathlib import Path
import pandas as pd
import streamlit as st


MODEL_RESULTS_FILE = Path("/Users/ignaciagothe/Desktop/Modelamiento Pricing Klap/data/processed/merchant_pricing_model_results.parquet")
FEATURE_BASE_FILE = Path("/Users/ignaciagothe/Desktop/Modelamiento Pricing Klap/data/processed/merchant_pricing_feature_base.parquet")


@st.cache_data(show_spinner=False)
def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {path}")
    return pd.read_parquet(path)


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "—"
    if abs(value) >= 1e9:
        return f"${value/1e9:,.2f}B"
    if abs(value) >= 1e6:
        return f"${value/1e6:,.2f}MM"
    return f"${value:,.0f}"


def main() -> None:
    st.set_page_config(
        page_title="Modelo de Pricing Klap",
        page_icon="💳",
        layout="wide",
    )
    st.title("Modelo de Pricing Klap")
    st.caption(
        "Dashboard para explorar el modelo de márgenes, benchmarking competitivo y segmentación de comercios."
    )

    with st.spinner("Cargando datos..."):
        model_df = load_parquet(MODEL_RESULTS_FILE)
        feature_df = load_parquet(FEATURE_BASE_FILE)

    clusters = sorted(model_df["segmento_cluster_label"].dropna().unique())
    acciones = sorted(model_df["accion_sugerida"].dropna().unique())
    volumen_segmentos = (
        model_df["segmento_promedio_volumen"]
        .dropna()
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
        "Los filtros permiten priorizar grupos específicos para campañas de pricing o retención."
    )

    filtered = model_df[
        model_df["segmento_cluster_label"].isin(cluster_filter)
        & model_df["accion_sugerida"].isin(accion_filter)
        & model_df["segmento_promedio_volumen"].isin(segmento_filter)
    ].copy()

    total_volume = filtered["monto_total_anual"].sum()
    total_margin = filtered["margen_estimado"].sum()
    avg_margin_pct = filtered["margen_pct_volumen"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Volumen anual (CLP)", format_currency(total_volume))
    col2.metric("Margen estimado (CLP)", format_currency(total_margin))
    col3.metric(
        "Margen % promedio",
        f"{avg_margin_pct*100:.2f}%" if not math.isnan(avg_margin_pct) else "—",
    )

    st.subheader("Distribución por acción sugerida")
    action_summary = (
        filtered.groupby("accion_sugerida")
        .agg(
            comercios=("rut_comercio", "count"),
            volumen=("monto_total_anual", "sum"),
            margen=("margen_estimado", "sum"),
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

    st.subheader("Detalle por comercio")
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
    st.dataframe(
        filtered[detail_cols].sort_values("monto_total_anual", ascending=False),
        use_container_width=True,
    )

    st.subheader("Mix de marcas (Visa/Mastercard)")
    mix_cols = ["rut_comercio", "share_visa", "share_mastercard"]
    mix_df = (
        model_df.loc[model_df["rut_comercio"].isin(filtered["rut_comercio"]), mix_cols]
        .set_index("rut_comercio")
        .clip(0, 1)
    )
    st.dataframe(
        mix_df.style.format("{:.1%}"),
        use_container_width=True,
    )

    st.subheader("Notas")
    st.markdown(
        """
        - `margen_estimado` = ingresos (MDR + fijo) − costos mínimos (interchange + marca).
        - `gap_pricing_mdr` positivo indica que la tarifa de Klap supera el benchmark Transbank.
        - `segmento_cluster_label` permite trabajar con arquetipos de comercios para campañas escalables.
        - Para actualizar los datos vuelve a ejecutar el notebook y guarda los parquet en `data/processed/`.
        """
    )

    st.caption("Fuente: modelo de pricing 2024. Todos los montos en CLP.")


if __name__ == "__main__":
    main()
