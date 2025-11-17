#!/usr/bin/env python3
"""Quick script to check the newly added data files."""
import sys
try:
    import pandas as pd
    import openpyxl
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please run in notebook environment where openpyxl is available")
    sys.exit(1)

print("=" * 80)
print("BRAND COSTS FILE")
print("=" * 80)
try:
    brand_costs = pd.read_excel("costos_marca_25_1.xlsx")
    print(f"Shape: {brand_costs.shape}")
    print(f"\nColumns: {brand_costs.columns.tolist()}")
    print("\nFirst 10 rows:")
    print(brand_costs.head(10).to_string())
    print("\n\nSummary by Marca:")
    if "Marca" in brand_costs.columns and "Total costos de marca %" in brand_costs.columns:
        summary = brand_costs.groupby("Marca")["Total costos de marca %"].agg(["mean", "min", "max", "count"])
        print(summary)
except Exception as e:
    print(f"Error reading brand costs: {e}")

print("\n" + "=" * 80)
print("KLAP PRICING FILE")
print("=" * 80)
try:
    klap_pricing = pd.read_excel("Tarifas_Klap_2025.xlsx")
    print(f"Shape: {klap_pricing.shape}")
    print(f"\nColumns: {klap_pricing.columns.tolist()}")
    print("\nAll rows:")
    print(klap_pricing.to_string())
except Exception as e:
    print(f"Error reading Klap pricing: {e}")

print("\n" + "=" * 80)
print("INTERCHANGE RATES FILE")
print("=" * 80)
try:
    interchange = pd.read_csv("Tasa_Intercambio_Chile_Visa_y_Mastercard.csv")
    print(f"Shape: {interchange.shape}")
    print(f"\nColumns: {interchange.columns.tolist()}")
    print("\nMedian rates by Marca and Card Type (CP channel):")
    cp_data = interchange[interchange["Canal"] == "CP"]
    summary = cp_data.groupby(["Marca", "Tipo de tarjeta"])["TI %"].median()
    print(summary)
except Exception as e:
    print(f"Error reading interchange: {e}")
