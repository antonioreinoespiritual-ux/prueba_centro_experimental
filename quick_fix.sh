#!/bin/bash
# Script rápido para solucionar el problema de base de datos

echo "🔧 Solucionando problema de base de datos..."

# Crear directorio data si no existe
mkdir -p data

# Verificar si existe la base de datos
if [ -f "data/experiments.db" ]; then
    # Hacer backup con timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    echo "📦 Haciendo backup: data/experiments_backup_${TIMESTAMP}.db"
    cp data/experiments.db "data/experiments_backup_${TIMESTAMP}.db"

    # Eliminar base de datos antigua
    echo "🗑️  Eliminando base de datos antigua..."
    rm -f data/experiments.db
    echo "✅ Base de datos eliminada"
else
    echo "ℹ️  No se encontró base de datos existente"
fi

echo ""
echo "✅ ¡Listo! Ahora reinicia el servidor con:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "La base de datos se recreará automáticamente con el esquema correcto."
