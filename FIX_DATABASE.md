# Solución al Error de Base de Datos

## Problema
El error `sqlite3.OperationalError: no such column: experiment_records.views_finish_pct` ocurre porque la base de datos existente no tiene las columnas nuevas que fueron agregadas al modelo.

## Solución

### Opción 1: Usar el script de reset (Recomendado)

1. Detén el servidor uvicorn (presiona CTRL+C)
2. Ejecuta el script de reset:
   ```bash
   python reset_database.py
   ```
3. Reinicia el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

Este script:
- Crea un backup de tu base de datos actual (si existe)
- Elimina la base de datos antigua
- Crea una nueva con el esquema actualizado

### Opción 2: Eliminar manualmente la base de datos

1. Detén el servidor uvicorn (presiona CTRL+C)
2. Elimina la base de datos existente:
   ```bash
   rm -f data/experiments.db
   ```
3. Reinicia el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

Al reiniciar, la aplicación creará automáticamente una nueva base de datos con el esquema correcto.

### Opción 3: Migrar columnas nuevas sin borrar datos

Si quieres conservar la base de datos actual, ejecuta la migración:

```bash
python migrate_lean_hypothesis.py
```

Esto agrega columnas nuevas (como `threshold_value` y `volume_unit`) sin perder datos.

## Cambios Realizados

1. **Script de reset** (`reset_database.py`): Permite recrear la base de datos de forma segura
2. **CRUD actualizado** (`app/crud.py`): Ahora guarda todas las columnas nuevas:
   - Métricas de video orgánico: `video_url`, `views_finish_pct`, `retention_pct`, `avg_watch_time`, `video_duration`
   - Métricas de campaña publicitaria: `paid_video_duration`, `campaign_id`, `ad_set_id`, `ad_id`
   - Métricas de live: `live_viewers_peak`, `live_avg_viewers`, `live_duration`, `live_new_followers`

## Verificación

Después de aplicar la solución, deberías poder:
- Acceder a http://127.0.0.1:8000 sin errores
- Crear experimentos
- Guardar registros con todas las métricas
- Ver los datos en el dashboard sin errores "Internal Server Error"
