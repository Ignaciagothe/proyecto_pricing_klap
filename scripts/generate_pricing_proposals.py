"""
Genera la tabla merchant_pricing_proposals.parquet a partir de los resultados del modelo.

Ejecutar después de regenerar merchant_pricing_model_results.parquet y merchant_pricing_feature_base.parquet.
"""

from pathlib import Path
from typing import Dict, List
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

MODEL_FILE = DATA_DIR / "merchant_pricing_model_results.parquet"
FEATURE_FILE = DATA_DIR / "merchant_pricing_feature_base.parquet"
PRICING_FILE = BASE_DIR / "data" / "precios_actuales_klap.xlsx"
OUTPUT_FILE = DATA_DIR / "merchant_pricing_proposals.parquet"

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pricing_utils import (  # noqa: E402
    ASSUMED_MIX_DEFAULT,
    FALLBACK_SEGMENTS_DEFAULT,
    EffectiveRates,
    compute_effective_rates,
    refresh_pricing_metrics,
)

ADDONS: List[Dict] = [
    {
        "nombre": "Omnicanal Plus",
        "descripcion": "Incluye billeteras, QR, web checkout y soporte para marketplaces.",
        "fee_mensual": 35000,
        "criterio": lambda row: row.get("n_tecnologias_unicas", 0) < 2 and row.get("monto_total_anual", 0) > 60_000_000,
    },
    {
        "nombre": "Insights & Fidelización",
        "descripcion": "Reportes avanzados, campañas de puntos y marketing SMS/Email.",
        "fee_mensual": 25000,
        "criterio": lambda row: row.get("share_meses_activos", 0) > 0.6 and row.get("margen_estimado", 0) > 0,
    },
    {
        "nombre": "Pagos Internacionales",
        "descripcion": "Aceptación de tarjetas internacionales y pagos cross-border.",
        "fee_mensual": 45000,
        "criterio": lambda row: row.get("share_visa", 0) > 0.5 and row.get("monto_total_anual", 0) > 120_000_000,
    },
]


def construir_planes(effective_rates: EffectiveRates) -> List[Dict]:
    planes: List[Dict] = [
        {
            "nombre": "Plan Estándar",
            "segmento_origen": "Estándar",
            "descripcion": "Tarifa oficial para comercios con ventas hasta 8 MM CLP mensuales.",
            "segmentos_objetivo_volumen": ["Estándar", "Sin ventas"],
            "segmentos_objetivo_cluster": ["Baja actividad", "Margen en riesgo", "Brecha competitiva"],
        },
        {
            "nombre": "Plan PRO",
            "segmento_origen": "PRO",
            "descripcion": "Tarifa oficial PRO para comercios con 8-30 MM CLP mensuales.",
            "segmentos_objetivo_volumen": ["PRO", "Optimización gradual"],
            "segmentos_objetivo_cluster": ["Optimización gradual", "Brecha competitiva"],
        },
        {
            "nombre": "Plan PRO Max",
            "segmento_origen": "PRO Max",
            "descripcion": "Tarifa oficial PRO Max para comercios de alto volumen (>30 MM CLP).",
            "segmentos_objetivo_volumen": ["PRO Max", "Enterprise"],
            "segmentos_objetivo_cluster": ["Alta contribución"],
        },
    ]

    for plan in planes:
        seg = plan["segmento_origen"]
        if seg not in effective_rates.table.index:
            raise KeyError(f"Segmento {seg} no encontrado en la grilla oficial.")
        plan["mdr"] = float(effective_rates.mdr.loc[seg])
        plan["fijo"] = float(effective_rates.fijo.loc[seg])

    return planes


PLANES: List[Dict] = []
PLAN_COLUMNS = ["plan_recomendado", "plan_mdr_propuesto", "plan_fijo_propuesto", "addons_recomendados"]


def recomendar_plan(row: pd.Series) -> Dict[str, float]:
    if not PLANES:
        raise ValueError("No se han inicializado los planes de pricing.")
    score_plan = []
    for plan in PLANES:
        score = 0
        if row.get("segmento_promedio_volumen") in plan["segmentos_objetivo_volumen"]:
            score += 2
        if row.get("segmento_cluster_label") in plan["segmentos_objetivo_cluster"]:
            score += 2
        if row.get("monto_total_anual", 0) > 120_000_000 and plan["nombre"] == "Plan PRO Max":
            score += 1
        if row.get("monto_total_anual", 0) < 30_000_000 and plan["nombre"] == "Plan Estándar":
            score += 1
        if row.get("margen_estimado", 0) <= 0:
            score -= 1
        score_plan.append((plan["nombre"], plan["mdr"], plan["fijo"], score))
    score_plan.sort(key=lambda x: x[3], reverse=True)
    best = score_plan[0]
    return {
        "plan_recomendado": best[0],
        "plan_mdr_propuesto": best[1],
        "plan_fijo_propuesto": best[2],
    }


def recomendar_addons(row: pd.Series) -> str:
    sugeridos = []
    for addon in ADDONS:
        try:
            aplica = addon["criterio"](row)
        except Exception:
            aplica = False
        if aplica:
            sugeridos.append(f"{addon['nombre']} (${addon['fee_mensual']:,})")
    return ", ".join(sugeridos) if sugeridos else "Sin add-ons sugeridos"


def main() -> None:
    if not PRICING_FILE.exists():
        raise FileNotFoundError(f"No se encontró {PRICING_FILE}")

    effective_rates = compute_effective_rates(
        PRICING_FILE,
        assumed_mix=ASSUMED_MIX_DEFAULT,
        fallback_segments=FALLBACK_SEGMENTS_DEFAULT,
    )
    global PLANES  # noqa: PLW0603
    PLANES = construir_planes(effective_rates)

    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"No se encontró {MODEL_FILE}")
    model_df = pd.read_parquet(MODEL_FILE)
    model_df = model_df.drop(columns=[col for col in PLAN_COLUMNS if col in model_df.columns])
    model_df = refresh_pricing_metrics(model_df, effective_rates)

    if FEATURE_FILE.exists():
        feature_df = pd.read_parquet(FEATURE_FILE)
        feature_df = feature_df.drop(columns=[col for col in PLAN_COLUMNS if col in feature_df.columns])
        base_df = model_df.merge(feature_df, on="rut_comercio", how="left", suffixes=("", "_feature"))
    else:
        base_df = model_df.copy()

    base_df = refresh_pricing_metrics(base_df, effective_rates)

    plan_df = base_df.apply(recomendar_plan, axis=1, result_type="expand")
    base_df = pd.concat([base_df, plan_df], axis=1)
    base_df["addons_recomendados"] = base_df.apply(recomendar_addons, axis=1)

    # Persistir salidas actualizadas
    model_df.to_parquet(MODEL_FILE, index=False)
    base_df.to_parquet(OUTPUT_FILE, index=False)
    print(f"Archivo guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
