#!/usr/bin/env python
"""
Script de demostración del pipeline de limpieza mejorado.
Muestra cómo el pipeline agrupa crímenes por ciudad, categoría y período.
"""

import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

from apps.backend.pipeline.cleaning import clean_and_transform_data, validate_data_quality

# Crear un DataFrame de ejemplo con múltiples crímenes del mismo tipo
# en la misma ciudad, mes y año (simula datos reales de London Crime)
sample_data = pd.DataFrame({
    "borough": ["City of London", "City of London", "City of London", "Westminster", "Westminster", "Westminster"],
    "major_category": ["Theft and Handling", "Burglary", "Theft and Handling", "Theft and Handling", "Theft and Handling", "Violence Against the Person"],
    "minor_category": ["Pickpocketing", "Burglary", "Shoplifting", "Pickpocketing", "Shoplifting", "Assault"],
    "value": [15, 8, 22, 12, 8, 5],  # Diferentes incidentes del mismo mes/año/ciudad
    "year": [2024, 2024, 2024, 2024, 2024, 2024],
    "month": [1, 1, 1, 1, 1, 1],
})

print("=" * 80)
print("DEMOSTRACIÓN: Pipeline de Limpieza de Datos de Crimen en Londres")
print("=" * 80)

print("\n📊 DATOS ORIGINALES (SIN AGREGACIÓN):")
print(f"Total de registros: {len(sample_data)}")
print(sample_data[["borough", "major_category", "minor_category", "value", "year", "month"]])

print("\n" + "=" * 80)
print("🔄 EJECUTANDO PIPELINE DE LIMPIEZA...")
print("=" * 80)

# Ejecutar el pipeline
result = clean_and_transform_data(sample_data)

print("\n✅ DATOS DESPUÉS DEL PIPELINE (AGREGADOS POR CATEGORÍA):")
print(f"Total de registros: {len(result)}")
print(result[["borough", "major_category", "minor_category", "total_crimes", "year", "month"]])

print("\n📋 ESTRUCTURA FINAL DEL DATASET:")
print(f"Columnas: {list(result.columns)}")
print(f"Tipos de datos:\n{result.dtypes}")

print("\n✔️  VALIDANDO CALIDAD DE DATOS...")
is_valid = validate_data_quality(result)
print(f"✅ Dataset validado exitosamente: {is_valid}")

print("\n" + "=" * 80)
print("RESUMEN DE CAMBIOS:")
print("=" * 80)
print("✨ Cambios realizados:")
print("   1. Agregación por (borough, major_category, minor_category, year, month)")
print("   2. Suma de todos los crímenes para cada tipo/ubicación/período")
print("   3. Renombrada columna 'value' a 'total_crimes' para claridad")
print("   4. Se mantiene el desglose por tipo de crimen (categorías)")
print("   5. Dataset final optimizado y listo para Supabase")
print("\n💾 El pipeline está listo para enviar datos a Supabase con la estructura:")
print("   - borough: Ciudad")
print("   - major_category: Categoría principal de crimen")
print("   - minor_category: Subcategoría de crimen")
print("   - year: Año")
print("   - month: Mes")
print("   - total_crimes: Total de crímenes en esa categoría/ciudad/mes/año")
print("   - date: Fecha en formato datetime")
print("=" * 80)
