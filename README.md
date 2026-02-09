# Centro Experimental — Cloud Drive

## Backend (FastAPI)

### Dependencias
```bash
pip install -r requirements.txt
```

### Desarrollo
```bash
uvicorn app.main:app --reload
```

## Frontend Cloud Drive (Vite + React)

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
