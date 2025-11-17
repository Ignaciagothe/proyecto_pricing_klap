#!/bin/bash
# Script para limpiar outputs de notebooks antes de commit
# Uso: ./scripts/clean_notebooks.sh

echo "🧹 Limpiando outputs de notebooks..."

# Encontrar y limpiar todos los notebooks
find . -name "*.ipynb" -not -path "*/.ipynb_checkpoints/*" -exec \
    jupyter nbconvert --clear-output --inplace {} \;

echo "✅ Todos los notebooks han sido limpiados"
echo "⚠️  Recuerda ejecutar este script antes de hacer commit"
