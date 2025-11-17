"""Herramientas de análisis para churn funcional y calidad de datos de pricing.

Este script resume los hallazgos críticos del notebook y permite:
1. Validar coherencia entre `monto_clp` y `monto_adquriencia_general`.
2. Revisar que los costos de marca no estén en cero.
3. Clasificar terminales y comercios según actividad (churn formal, funcional y declive).
4. Exportar tablas de salud (opcional) para ser usadas en dashboards o notebooks.

Uso básico:
    python scripts/analisis_churn_y_calidad.py \
        --base-csv base_con_sin_trx_cleaned.csv \
        --brand-costs data/costos_marca_25_1.xlsx \
        --output-dir data/processed

El script solo lee archivos locales; no modifica fuentes originales.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

BAJA_ESTADOS = {"BAJA", "PROCESO_BAJA", "BAJA_POR_PERDIDA"}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analiza churn y consistencia de la base de pricing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--base-csv",
        type=Path,
        default=Path("base_con_sin_trx_cleaned.csv"),
        help="Ruta al CSV principal con transacciones por terminal",
    )
    parser.add_argument(
        "--brand-costs",
        type=Path,
        default=Path("data/costos_marca_25_1.xlsx"),
        help="Ruta al Excel con costos de marca (opcional pero recomendado)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio donde guardar tablas resumidas (CSV). Si no se entrega, solo imprime resúmenes",
    )
    return parser.parse_args(argv)


def parse_numeric_date(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    valid = numeric.notna()
    if valid.any():
        numeric_int = numeric[valid].round().astype("Int64")
        formatted = numeric_int.astype(str).str.zfill(8)
        parsed = pd.to_datetime(formatted, format="%Y%m%d", errors="coerce")
        result.loc[valid] = parsed.values
    return result


def load_base_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró la base principal: {path}")
    df = pd.read_csv(path, low_memory=False)
    required_cols = {
        "periodo",
        "rut_comercio",
        "numero_terminal",
        "estado_terminal",
        "fecha_instalacion",
        "fecha_baja",
        "monto_clp",
        "monto_adquriencia_general",
        "qtrx_total",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Faltan columnas requeridas en la base principal: {sorted(missing)}")

    df = df.copy()
    df["periodo"] = pd.to_datetime(df["periodo"] + "-01", format="%Y-%m-%d", errors="coerce").dt.to_period("M")
    df["fecha_instalacion"] = parse_numeric_date(df["fecha_instalacion"])
    df["fecha_baja"] = parse_numeric_date(df["fecha_baja"])
    df["monto_clp"] = pd.to_numeric(df["monto_clp"], errors="coerce").fillna(0)
    df["monto_adquriencia_general"] = pd.to_numeric(
        df["monto_adquriencia_general"], errors="coerce"
    ).fillna(0)
    df["qtrx_total"] = pd.to_numeric(df["qtrx_total"], errors="coerce").fillna(0)
    return df


def summarize_value_gap(df: pd.DataFrame) -> pd.DataFrame:
    diff = df["monto_clp"] - df["monto_adquriencia_general"]
    summary = {
        "filas": len(df),
        "abs_sum_diff": float(diff.abs().sum()),
        "max_abs_diff": float(diff.abs().max()),
        "share_exact_match": float(diff.eq(0).mean()),
        "p50_abs_diff": float(diff.abs().median()),
        "p90_abs_diff": float(diff.abs().quantile(0.9)),
    }
    return pd.DataFrame(summary, index=[0])


def summarize_brand_costs(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        print(f"⚠️  No se encontró el archivo de costos de marca: {path}")
        return None
    brand_df = pd.read_excel(path)
    if "Marca" not in brand_df.columns or "Total costos de marca %" not in brand_df.columns:
        raise KeyError("El Excel de costos debe contener 'Marca' y 'Total costos de marca %'")
    summary = (
        brand_df.groupby("Marca")["Total costos de marca %"].agg(["mean", "min", "max", "std"])
    )
    return summary


def build_terminal_health(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("numero_terminal")
        .agg(
            rut_comercio=("rut_comercio", "first"),
            monto_total=("monto_adquriencia_general", "sum"),
            qtrx_total=("qtrx_total", "sum"),
            meses_reportados=("periodo", "nunique"),
            meses_activos=("qtrx_total", lambda s: (s > 0).sum()),
            fecha_instalacion=("fecha_instalacion", "min"),
            fecha_baja=("fecha_baja", "max"),
            estado_final=("estado_terminal", lambda s: s.iloc[-1]),
        )
        .reset_index()
    )

    condiciones = [
        grouped["fecha_baja"].notna(),
        grouped["qtrx_total"].eq(0),
        grouped["meses_activos"].eq(0),
        grouped["meses_activos"].lt(3),
    ]
    etiquetas = ["CHURNED", "NUNCA_ACTIVA", "INACTIVA", "IRREGULAR"]
    grouped["estado_funcional"] = np.select(condiciones, etiquetas, default="ACTIVA")
    return grouped


def build_merchant_health(df: pd.DataFrame) -> pd.DataFrame:
    merchant_month = (
        df.groupby(["rut_comercio", "periodo"], as_index=False)
        .agg(
            monto_tarjetas=("monto_adquriencia_general", "sum"),
            qtrx_total=("qtrx_total", "sum"),
            n_terminales=("numero_terminal", "nunique"),
        )
        .rename(columns={"monto_tarjetas": "monto_periodo"})
    )

    agg = (
        merchant_month.groupby("rut_comercio")
        .agg(
            monto_total_anual=("monto_periodo", "sum"),
            qtrx_total_anual=("qtrx_total", "sum"),
            meses_reportados=("periodo", "nunique"),
            meses_activos=("monto_periodo", lambda s: (s > 0).sum()),
            monto_promedio_mensual=("monto_periodo", "mean"),
            monto_max_mensual=("monto_periodo", "max"),
            n_terminales_max=("n_terminales", "max"),
        )
        .reset_index()
    )
    agg["share_meses_activos"] = np.where(
        agg["meses_reportados"] > 0,
        agg["meses_activos"] / agg["meses_reportados"],
        0.0,
    )

    terminales_activos = (
        df[df["qtrx_total"] > 0]
        .groupby("rut_comercio")["numero_terminal"]
        .nunique()
        .rename("n_terminales_activos")
    )
    agg = agg.merge(terminales_activos, on="rut_comercio", how="left")
    agg["n_terminales_activos"] = agg["n_terminales_activos"].fillna(0).astype(int)
    agg["terminal_utilization"] = np.where(
        agg["n_terminales_max"] > 0,
        agg["n_terminales_activos"] / agg["n_terminales_max"],
        0.0,
    )

    churn_flags = (
        df.groupby("rut_comercio")
        .agg(
            tiene_baja=("fecha_baja", lambda s: s.notna().any()),
            estado_baja=(
                "estado_terminal",
                lambda s: any(str(x).upper() in BAJA_ESTADOS for x in s.dropna())
            ),
        )
        .reset_index()
    )
    agg = agg.merge(churn_flags, on="rut_comercio", how="left")
    agg["churn_formal"] = agg["tiene_baja"] | agg["estado_baja"]

    agg["churn_label"] = agg.apply(classify_churn_row, axis=1)
    return agg


def classify_churn_row(row: pd.Series) -> str:
    share = row.get("share_meses_activos", 0.0)
    promedio = row.get("monto_promedio_mensual", 0.0)
    maximo = row.get("monto_max_mensual", 0.0)

    if row.get("churn_formal", False):
        return "Churn Formal"
    if share < 0.2:
        return "At-Risk Alto"
    if share < 0.5 and maximo > 0 and promedio < 0.6 * maximo:
        return "Declining"
    if share >= 0.7:
        return "Healthy"
    return "Irregular"


def maybe_save(df: pd.DataFrame, name: str, output_dir: Optional[Path]) -> None:
    if output_dir is None:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"💾 Guardado: {path}")


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    df = load_base_table(args.base_csv)

    print("\n📊 Validación de montos (`monto_clp` vs `monto_adquriencia_general`):")
    gap_summary = summarize_value_gap(df)
    print(gap_summary.to_string(index=False))

    if args.brand_costs is not None:
        brand_summary = summarize_brand_costs(args.brand_costs)
        if brand_summary is not None:
            print("\n🏷️  Resumen de costos de marca (%):")
            print(brand_summary.to_string())
            maybe_save(brand_summary.reset_index(), "resumen_costos_marca", args.output_dir)

    print("\n🔍 Clasificación de terminales por actividad:")
    terminal_health = build_terminal_health(df)
    print(terminal_health["estado_funcional"].value_counts().to_string())
    maybe_save(terminal_health, "terminal_health", args.output_dir)

    print("\n👥 Salud de comercios (churn funcional):")
    merchant_health = build_merchant_health(df)
    print(merchant_health["churn_label"].value_counts().to_string())
    maybe_save(merchant_health, "merchant_health", args.output_dir)

    print("\n✅ Análisis completado. Usa las tablas guardadas para profundizar en el notebook o dashboard.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entrypoint
        print(f"❌ Error durante el análisis: {exc}", file=sys.stderr)
        sys.exit(1)
