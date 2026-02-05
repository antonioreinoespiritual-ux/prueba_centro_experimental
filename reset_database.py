#!/usr/bin/env python3
"""
Script para recrear la base de datos con el esquema actualizado.
Este script elimina la base de datos existente y crea una nueva con todas las tablas.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

from app.database import Base, engine, DATABASE_URL


def reset_database():
    """Elimina y recrea la base de datos."""

    # Extraer la ruta del archivo de la URL de la base de datos
    # DATABASE_URL es como "sqlite:///./data/experiments.db"
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_file = Path(db_path)

    # Crear el directorio data/ si no existe
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Hacer backup si existe la base de datos
    if db_file.exists():
        backup_name = f"experiments_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = db_file.parent / backup_name
        print(f"📦 Haciendo backup de la base de datos en: {backup_path}")
        shutil.copy2(db_file, backup_path)

        # Eliminar la base de datos actual
        print(f"🗑️  Eliminando base de datos antigua: {db_file}")
        db_file.unlink()
    else:
        print(f"ℹ️  No existe base de datos previa en: {db_file}")

    # Crear todas las tablas con el nuevo esquema
    print("🏗️  Creando tablas con el esquema actualizado...")
    Base.metadata.create_all(bind=engine)

    print("✅ Base de datos recreada exitosamente!")
    print(f"📍 Ubicación: {db_file.absolute()}")


if __name__ == "__main__":
    reset_database()
