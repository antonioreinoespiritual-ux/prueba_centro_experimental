# Centro Experimental — Cloud Drive

## Backend (FastAPI)

### Dependencias
```bash
pip install -r requirements.txt
```

### Configuración de almacenamiento local
```bash
export CLOUD_ROOT=/Users/m2/CloudDriveData
mkdir -p /Users/m2/CloudDriveData
```

### Desarrollo
```bash
uvicorn app.main:app --reload
```


## Frontend Home (React + Vite)

### Desarrollo
```bash
cd frontend/home
npm install
npm run dev
```

### Build para producción (servido por FastAPI en /)
```bash
cd frontend/home
npm install
npm run build
```

El build genera los assets en `static/home/`.

## Frontend Cloud Drive (Vite + React)

### Configuración API
```bash
export VITE_API_URL=http://127.0.0.1:8000
```

### Desarrollo
```bash
cd frontend/cloud
npm install
npm run dev
```

### Build para producción (servido por FastAPI en /cloud)
```bash
cd frontend/cloud
npm install
npm run build
```

El build genera los assets en `static/cloud/` y el backend los sirve desde `/cloud`.

## Producción
1. Compila el frontend (`npm run build`).
2. Levanta el backend con `uvicorn app.main:app`.

## API Cloud Drive (ejemplos rápidos)

### Crear biblioteca
```bash
curl -X POST http://127.0.0.1:8000/api/cloud/libraries \
  -H "Content-Type: application/json" \
  -d '{"name":"Biblioteca Principal"}'
```

### Listar bibliotecas
```bash
curl http://127.0.0.1:8000/api/cloud/libraries
```

### Crear carpeta
```bash
curl -X POST http://127.0.0.1:8000/api/cloud/folders \
  -H "Content-Type: application/json" \
  -d '{"name":"Creatives","library_id":1}'
```

### Listar items raíz
```bash
curl "http://127.0.0.1:8000/api/cloud/items?library_id=1"
```

### Subir archivo
```bash
curl -X POST http://127.0.0.1:8000/api/cloud/files/complete-upload \
  -F "file=@/path/to/file.pdf" \
  -F "filename=file.pdf" \
  -F "library_id=1"
```

### Descargar archivo
```bash
curl -L "http://127.0.0.1:8000/api/cloud/files/1/download" -o archivo.pdf
```

## Drive Sync (Projects/Hypotheses/Records)

### Bootstrap de carpetas base
```bash
curl -X POST http://127.0.0.1:8000/api/drive-sync/bootstrap
```

### Backfill de hipótesis y records existentes
```bash
curl -X POST http://127.0.0.1:8000/api/drive-sync/backfill
```
Respuesta incluye `project_consolidated` y `project_consolidated_items` cuando se fusionan carpetas legacy `P*`.

### Sincronizar una hipótesis específica
```bash
curl -X POST http://127.0.0.1:8000/api/drive-sync/hypotheses/1
```

### Sincronizar un record específico
```bash
curl -X POST http://127.0.0.1:8000/api/drive-sync/records/1
```

### Listar proyectos y sus hipótesis
```bash
curl http://127.0.0.1:8000/api/cloud/projects
curl http://127.0.0.1:8000/api/cloud/projects/1/hypotheses
```

### Estructura esperada en disco
```
<CLOUD_ROOT>/Projects/
  <project_slug>/
    Hypotheses/
      H<experiment_id>_<slug_independent_variable>/
        Records/
          R<record_id>_<slug_record_name>/
<CLOUD_ROOT>/_System
<CLOUD_ROOT>/_Archived
```

## Smoke test (filesystem real)
1. Crea una biblioteca y confirma que existe en `/Users/m2/CloudDriveData`.
2. Desde la UI crea una carpeta “Docs” y verifica en Finder/terminal.
3. Sube `test.txt` y confirma que el archivo aparece físicamente.
4. Renombra, mueve y borra desde la UI; verifica en disco.
5. Descarga el archivo desde la UI y valida el contenido.
6. Crea una hipótesis y verifica la carpeta en `Projects/<project_slug>/Hypotheses/H<ID>_<slug>`.
7. Crea un record y verifica la carpeta en `Projects/<project_slug>/Hypotheses/H<ID>_<slug>/Records/R<ID>_<slug>`.
8. Ejecuta el backfill para crear carpetas faltantes.
