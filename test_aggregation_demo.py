#!/usr/bin/env python
"""
Script que demuestra la agregación de crímenes con datos repetidos.
Muestra cómo el pipeline suma múltiples incidentes del mismo tipo.
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

from apps.backend.pipeline.cleaning import aggregate_crime_data, create_date_column, remove_unnecessary_columns

# Crear un DataFrame con múltiples incidentes del MISMO crimen
# en la misma ubicación, período y categoría (datos duplicados que deben sumarse)
sample_data = pd.DataFrame({
    "borough": ["City of London", "City of London", "City of London", "City of London"],
    "major_category": ["Theft and Handling", "Theft and Handling", "Theft and Handling", "Burglary"],
    "minor_category": ["Pickpocketing", "Pickpocketing", "Pickpocketing", "Burglary"],
    "value": [5, 7, 8, 10],  # 4 registros del MISMO crimen (misma categoría, ciudad y mes/año)
    "year": [2024, 2024, 2024, 2024],
    "month": [1, 1, 1, 1],
})

print("=" * 90)
print("DEMOSTRACIÓN: AGREGACIÓN DE CRÍMENES DUPLICADOS")
print("=" * 90)

print("\n📊 DATOS ORIGINALES (4 registros de Pickpocketing en la misma ciudad/mes/año):")
print(sample_data[["borough", "major_category", "minor_category", "value", "year", "month"]])
print(f"Total incidentes sin agregación: {sample_data['value'].sum()}")

print("\n🔄 APLICANDO AGREGACIÓN...")
result = aggregate_crime_data(sample_data)
result = create_date_column(result)
result = remove_unnecessary_columns(result)

print("\n✅ DATOS DESPUÉS DE AGREGACIÓN:")
print(result[["borough", "major_category", "minor_category", "total_crimes", "year", "month"]])

print("\n📊 DESGLOSE POR CATEGORÍA:")
breakdown = result.groupby("major_category")["total_crimes"].sum()
for category, total in breakdown.items():
    print(f"   • {category}: {total} crímenes")

print("\n" + "=" * 90)
print("RESULTADO:")
print("=" * 90)
print(f"✨ Registros originales: {len(sample_data)}")
print(f"✨ Registros después de agregación: {len(result)}")
print(f"✨ Reducción: {len(sample_data) - len(result)} registros (consolidados)")
print(f"\n💡 Los 3 registros de 'Pickpocketing' (5+7+8=20) se agregaron en 1 registro")
print(f"💡 El 1 registro de 'Burglary' (10) se mantiene igual")
print("\n" + "=" * 90)
