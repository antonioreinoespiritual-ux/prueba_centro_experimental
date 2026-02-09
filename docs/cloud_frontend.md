# Cloud Drive Frontend

## Requisitos
- Node.js 18+

## Desarrollo (frontend)
```bash
cd frontend/cloud
npm install
npm run dev
```

## Build (servir desde /cloud)
```bash
cd frontend/cloud
npm install
npm run build
```

El build exporta los archivos a `static/cloud/` para que FastAPI los sirva en `/cloud`.
