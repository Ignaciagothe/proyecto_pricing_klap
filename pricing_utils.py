from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Union

import numpy as np
import pandas as pd


ASSUMED_MIX_DEFAULT: Mapping[str, float] = {
    "Crédito": 0.6,
    "Débito": 0.35,
    "Prepago": 0.05,
}

# target_segment -> source_segment (None => set zeros)
FALLBACK_SEGMENTS_DEFAULT: Mapping[str, Optional[str]] = {
    "Enterprise": "PRO Max",
    "Sin ventas": None,
}

ACTION_THRESHOLDS_DEFAULT = {
    "margin_threshold": 0.0,
    "competition_threshold": 0.0015,
    "inactivity_threshold": 0.2,
}


@dataclass(frozen=True)
class EffectiveRates:
    """Container for effective MDR and fixed fee by segment."""

    table: pd.DataFrame

    @property
    def mdr(self) -> pd.Series:
        return self.table["mdr_effectivo"]

    @property
    def fijo(self) -> pd.Series:
        return self.table["fijo_effectivo"]


def compute_effective_rates(
    pricing_source: Union[Path, str, pd.DataFrame],
    *,
    assumed_mix: Optional[Mapping[str, float]] = None,
    fallback_segments: Optional[Mapping[str, Optional[str]]] = None,
) -> EffectiveRates:
    """Return weighted MDR/fixed fee per segmento using the provided pricing grid.

    Accepts either a path to an Excel file or a precalculated DataFrame with the same columns.
    """
    if isinstance(pricing_source, (str, Path)):
        pricing_path = Path(pricing_source)
        if not pricing_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de precios oficiales: {pricing_path}")
        pricing_grid = pd.read_excel(pricing_path)
    elif isinstance(pricing_source, pd.DataFrame):
        pricing_grid = pricing_source.copy()
    else:
        raise TypeError("`pricing_source` debe ser una ruta a Excel o un DataFrame preconstruido.")

    mix = dict(assumed_mix or ASSUMED_MIX_DEFAULT)
    if not mix:
        raise ValueError("El mix de medios no puede ser vacío.")

    if "Variable %" not in pricing_grid.columns:
        raise KeyError("La grilla de precios debe contener la columna 'Variable %'.")

    pricing_grid = pricing_grid.copy()
    pricing_grid["Variable_pct"] = pricing_grid["Variable %"] / 100.0
    pricing_matrix = pricing_grid.pivot_table(
        index="Segmento",
        columns="Medio",
        values=["Variable_pct", "Fijo CLP (aprox)"],
    )

    var_matrix = pricing_matrix.xs("Variable_pct", level=0, axis=1)
    fijo_matrix = pricing_matrix.xs("Fijo CLP (aprox)", level=0, axis=1)

    def _weighted_value(values: pd.Series) -> float:
        total = 0.0
        for medio, share in mix.items():
            valor = values.get(medio, np.nan)
            if pd.notna(valor):
                total += share * float(valor)
        return float(total)

    rates = pd.DataFrame(
        {
            "mdr_effectivo": var_matrix.apply(_weighted_value, axis=1),
            "fijo_effectivo": fijo_matrix.apply(_weighted_value, axis=1),
        }
    )

    fallback = fallback_segments or FALLBACK_SEGMENTS_DEFAULT
    rates = _apply_fallback_segments(rates, fallback)
    return EffectiveRates(table=rates)


def _apply_fallback_segments(
    rates: pd.DataFrame,
    fallback_segments: Mapping[str, Optional[str]],
) -> pd.DataFrame:
    """Ensure required segments exist, cloning or zeroing as requested."""
    if "mdr_effectivo" not in rates.columns or "fijo_effectivo" not in rates.columns:
        raise KeyError("La tabla de tarifas debe contener 'mdr_effectivo' y 'fijo_effectivo'.")

    rates = rates.copy()
    for target, source in fallback_segments.items():
        if target in rates.index:
            continue
        if source is None:
            rates.loc[target] = {"mdr_effectivo": 0.0, "fijo_effectivo": 0.0}
        else:
            if source not in rates.index:
                raise KeyError(f"No se puede crear el segmento '{target}' porque '{source}' no existe.")
            rates.loc[target] = rates.loc[source]
    return rates.sort_index()


def apply_effective_rates(
    df: pd.DataFrame,
    effective_rates: EffectiveRates,
    *,
    segment_col: str = "segmento_promedio_volumen",
    mdr_col: str = "klap_mdr",
    fijo_col: str = "klap_fijo_clp",
) -> pd.DataFrame:
    """Assign effective MDR/fijo by segment; defaults to cero when missing."""
    result = df.copy()
    segments = result.get(segment_col, pd.Series(index=result.index, dtype="object")).astype("string")

    mdr_map = effective_rates.mdr
    fijo_map = effective_rates.fijo

    result[mdr_col] = segments.map(mdr_map).fillna(0.0).astype(float)
    result[fijo_col] = segments.map(fijo_map).fillna(0.0).astype(float)
    return result


def recompute_margin_metrics(
    df: pd.DataFrame,
    *,
    volume_col: str = "monto_total_anual",
    qtrx_col: str = "qtrx_total_anual",
    cost_col: str = "costo_min_estimado",
    mdr_col: str = "klap_mdr",
    fijo_col: str = "klap_fijo_clp",
) -> pd.DataFrame:
    """Update ingresos y márgenes usando MDR/fijo vigentes."""
    result = df.copy()
    volume = result.get(volume_col, 0).fillna(0.0).astype(float)
    qtrx = result.get(qtrx_col, 0).fillna(0.0).astype(float)
    mdr = result.get(mdr_col, 0).fillna(0.0).astype(float)
    fijo = result.get(fijo_col, 0).fillna(0.0).astype(float)
    cost = result.get(cost_col, 0).fillna(0.0).astype(float)

    result["ingreso_variable"] = volume * mdr
    result["ingreso_fijo"] = qtrx * fijo
    result["ingreso_total_klap"] = result["ingreso_variable"] + result["ingreso_fijo"]
    result["margen_estimado"] = result["ingreso_total_klap"] - cost
    with np.errstate(divide="ignore", invalid="ignore"):
        result["margen_pct_volumen"] = np.where(
            volume > 0,
            result["margen_estimado"] / volume,
            np.nan,
        )
    return result


def recompute_gap_metric(
    df: pd.DataFrame,
    *,
    rate_col: str = "klap_mdr",
    benchmark_col: str = "competidor_mdr",
    output_col: str = "gap_pricing_mdr",
) -> pd.DataFrame:
    """Refresh competitive gap vs. benchmark MDR."""
    result = df.copy()
    rate = result.get(rate_col, 0).fillna(0.0).astype(float)
    benchmark = result.get(benchmark_col, 0).fillna(0.0).astype(float)
    result[output_col] = rate - benchmark
    return result


def recompute_action_labels(
    df: pd.DataFrame,
    *,
    margin_threshold: float = ACTION_THRESHOLDS_DEFAULT["margin_threshold"],
    competition_threshold: float = ACTION_THRESHOLDS_DEFAULT["competition_threshold"],
    inactivity_threshold: float = ACTION_THRESHOLDS_DEFAULT["inactivity_threshold"],
) -> pd.Series:
    """Classify suggested action per comercio using business thresholds."""
    volume = df.get("monto_total_anual", pd.Series(index=df.index, dtype=float)).fillna(0.0).astype(float)
    margin = df.get("margen_estimado", pd.Series(index=df.index, dtype=float)).fillna(0.0).astype(float)
    gap = df.get("gap_pricing_mdr", pd.Series(index=df.index, dtype=float)).fillna(0.0).astype(float)
    activos = df.get("share_meses_activos", pd.Series(index=df.index, dtype=float)).fillna(0.0).astype(float)

    conditions = [
        volume.eq(0),
        margin <= margin_threshold,
        gap > competition_threshold,
        activos < inactivity_threshold,
    ]
    options = [
        "Reactivación comercial",
        "Ajustar MDR urgente",
        "Revisar competitividad",
        "Monitorear baja actividad",
    ]
    labels = np.select(conditions, options, default="Mantener / Upsell servicios")
    return pd.Series(labels, index=df.index, name="accion_sugerida")


def refresh_pricing_metrics(
    df: pd.DataFrame,
    effective_rates: EffectiveRates,
    *,
    thresholds: Optional[Mapping[str, float]] = None,
) -> pd.DataFrame:
    """Apply tariffs, recompute margin/gap, and refresh suggested actions."""
    result = apply_effective_rates(df, effective_rates)
    result = recompute_margin_metrics(result)
    result = recompute_gap_metric(result)

    thresh = dict(ACTION_THRESHOLDS_DEFAULT)
    if thresholds:
        thresh.update(thresholds)
    result["accion_sugerida"] = recompute_action_labels(result, **thresh)
    return result


__all__ = [
    "ASSUMED_MIX_DEFAULT",
    "FALLBACK_SEGMENTS_DEFAULT",
    "ACTION_THRESHOLDS_DEFAULT",
    "EffectiveRates",
    "apply_effective_rates",
    "compute_effective_rates",
    "recompute_action_labels",
    "recompute_gap_metric",
    "recompute_margin_metrics",
    "refresh_pricing_metrics",
]
