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

## Frontend Hypotheses (Vite + React)

### Configuración API
```bash
export VITE_API_URL=http://127.0.0.1:8000
```

### Desarrollo
```bash
cd frontend/hypotheses
npm install
npm run dev
```

### Build para producción (servido por FastAPI en /hypotheses)
```bash
cd frontend/hypotheses
npm install
npm run build
```

El build genera los assets en `static/hypotheses/` y el backend los sirve desde `/hypotheses`.


## Frontend Home (React + Vite)

Home modernizado en `frontend/home` y servido por FastAPI en `/` usando build estático en `static/home`.

### Desarrollo
```bash
cd frontend/home
npm install
npm run dev
```

### Build para producción (FastAPI en `/`)
```bash
cd frontend/home
npm install
npm run build
```

El build genera assets en `static/home/`. FastAPI usa `static/home/index.html` como Home principal y conserva `static/index.html` como fallback legacy.

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

## Entrevistas (Vite + React)

Nuevo módulo en `frontend/interviews` servido en `/interviews` (build estático en `static/interviews`).

### Desarrollo
```bash
cd frontend/interviews
npm install
npm run dev
```

### Build para producción (FastAPI)
```bash
cd frontend/interviews
npm install
npm run build
```

Luego abrir:
- `http://127.0.0.1:8000/interviews`

API usada por el módulo:
- `GET/POST/PATCH/DELETE /api/interviews/templates`
- `GET/POST/PATCH/DELETE /interviews/sessions (legacy)`
- `GET /api/interviews/projects/{project_id}/templates`
- `GET /interviews/projects/{project_id}/sessions (legacy)`

### Entrevistas CRM + Wizard + Adjuntos

Endpoints nuevos:
- `GET/POST/PATCH/DELETE /clients`
- `GET /clients/{id}/interviews`
- `POST /api/interviews`
- `GET /api/interviews?project_id=&hypothesis_id=&client_id=&campaign_id=&limit=&offset=`
- `GET /api/interviews/{id}`
- `PATCH /api/interviews/{id}`
- `POST /api/interviews/{id}/attachments` (multipart)
- `GET /api/interviews/{id}/attachments`
- `DELETE /api/attachments/{id}`

Almacenamiento de adjuntos:
- Archivos de transcripción en `data/uploads/interviews/{session_id}/`
- Metadata en tabla `interview_attachments`

Build frontend entrevistas:
```bash
cd frontend/interviews
npm install
npm run build
```


### Campañas de investigación

El módulo de Entrevistas ahora incluye una pestaña **Campaña de investigación** para gestionar recolección jerárquica de datos.

Endpoints:
- `GET /api/campaigns?project_id=&status=&search=`
- `GET /api/campaigns/{id}`
- `POST /api/campaigns`
- `PATCH /api/campaigns/{id}`
- `DELETE /api/campaigns/{id}`
- `GET /api/campaigns/{id}/clients`
- `GET /api/campaigns/{id}/templates`
- `GET /api/campaigns/{id}/interviews`

Reglas implementadas:
- Validación de consistencia `project_id` + `hypothesis_id` al crear/editar campañas.
- `Client`, `InterviewTemplate` e `InterviewSession` **requieren** `campaign_id` (campaña obligatoria).
- Para compatibilidad histórica, la migración crea automáticamente una **Campaña default** por proyecto y asigna registros antiguos sin campaña.


## Frontend QA

Checklist de validación visual/UX (Research OS):

- [ ] `/` Home: carga con header, cards y navegación operativa (sin rutas rotas).
- [ ] `/cloud`: UI renderiza y mantiene estilos del design system.
- [ ] `/hypotheses`: UI renderiza correctamente y mantiene layout consistente.
- [ ] `/interviews`: UI renderiza correctamente con tabs, estados loading/empty/error.
- [ ] Botones del Home (`Chat`, `Dashboard`, `Proyectos`, `Records`, `Públicos`, `Entrevistas`, `Cloud`, `Hypotheses`) abren páginas HTML/SPA (no JSON crudo).
- [ ] Ruta de Públicos UI: `/publics-app` (no colisiona con API `/publics/*`).
- [ ] Listados de Clientes/Plantillas/Entrevistas permiten filtrar por campaña y muestran campaña asociada.
- [ ] Formularios de Clientes/Plantillas/Entrevistas bloquean guardar sin campaña y muestran mensajes claros.
- [ ] Modales: cierre por botón, foco usable por teclado, confirmaciones de borrado activas.
- [ ] Toasts de éxito/error visibles en operaciones CRUD.
