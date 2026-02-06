# UI/UX Upgrade — Centro Experimental

## Resumen

Rediseno visual completo del frontend: de un look claro basico a una estetica **dark premium + glass subtle** tipo SaaS de primer nivel. Se mantuvo 100% de la funcionalidad existente sin cambiar endpoints ni contratos con el backend.

---

## Que cambio

### Design System (`static/css/design-system.css`)
- **Tokens centralizados**: colores (surface, glass, text, semantic, channel), spacing, radius, shadows, tipografia
- **Componentes reutilizables**: Card, StatChip, KpiCard, Badge, Table, Modal, Toast, GuideCard, Timeline, EvalPanel, HypothesisPanel
- **Fuente**: Inter via Google Fonts
- **Tema**: Dark premium con glass morphism (backdrop-filter blur)
- **Responsive**: Breakpoints en 768px, 980px, 1200px
- **Accesibilidad**: focus-visible, aria-labels, roles, contraste AA
- **Print**: Estilos para impresion

### index.html (Centro Experimental)
- Layout con `app-container` centrado
- Top bar con titulo gradiente y navegacion
- Modelo Conceptual Lean como `guide-card` con pasos numerados
- Formularios de records (LIVE/ORGANIC/PAID) con border-left de color por canal
- Secciones con `field-section` dividers
- Toast notifications en vez de `alert()`

### dashboard.html (Dashboard Experimental)
- Filtros en `grid-3` dentro de card glass
- Hypothesis panel con gradiente brand
- Evaluation panel con grid de metricas y badges semanticos
- Modal de Analisis IA con estilos premium
- Tablas con `table-wrapper`, sticky headers, zebra sutil
- Timeline con items hover
- Badges de estado con colores semanticos (validated=verde, invalidated=rojo, etc.)
- Toast notifications para acciones criticas
- Loading states con spinner animado

### records.html (Lista de Records)
- Filtros avanzados en grid responsive
- Tabla con badges de canal y estado
- Tarjeta de detalle con stat-chips
- Navegacion consistente

### stats_dashboard.html (Analisis Estadistico)
- Selector de experimentos con hypothesis panels
- KPI cards para metricas
- Comparison grid para tablas de comparacion
- Charts SVG con colores del design system (#7c6cff, #34d399)
- Significance badges (success/danger)
- Export CSV con boton secondary

---

## Como validar que nada se rompio

### Checklist de prueba manual

1. **Centro Experimental (index.html)**
   - [ ] Crear un experimento nuevo con todos los campos
   - [ ] Verificar que el select de experimentos se actualiza
   - [ ] Crear record LIVE con metricas
   - [ ] Crear record ORGANICO con metricas
   - [ ] Crear record PAID con metricas
   - [ ] Actualizar un record existente (close)
   - [ ] Toast aparece en lugar de alert

2. **Dashboard (dashboard.html)**
   - [ ] Carga inicial muestra datos
   - [ ] Filtro por traffic type funciona
   - [ ] Seleccionar experimento muestra hypothesis panel
   - [ ] Boton "Evaluar" muestra grid de evaluacion
   - [ ] Boton "Aplicar Resultado" cambia estado
   - [ ] Boton "ANALISIS IA" abre modal y muestra analisis
   - [ ] Cerrar modal con boton o click fuera
   - [ ] Vista 1: Aprendizaje Validado ordena correctamente
   - [ ] Vista 2: Hipotesis Vivas vs Muertas agrupa
   - [ ] Vista 3: Aprendizaje Acumulado muestra patrones
   - [ ] Vista 4: Detalle con timeline
   - [ ] Records del experimento: click en row muestra tarjeta
   - [ ] Toast notifications funcionan

3. **Records (records.html)**
   - [ ] Filtros avanzados aplican correctamente
   - [ ] Limpiar filtros resetea todo
   - [ ] Click en record muestra tarjeta de detalle
   - [ ] Badges de status y canal visibles

4. **Stats Dashboard (stats_dashboard.html)**
   - [ ] Seleccionar Experimento A y B
   - [ ] Boton "Analizar y Comparar" muestra resultados
   - [ ] Hypothesis panels aparecen
   - [ ] Graficos SVG renderizan
   - [ ] Export CSV descarga archivo
   - [ ] Tests de significancia muestran badges

5. **Responsive**
   - [ ] Movil (375px): todo legible, grids colapsan a 1 columna
   - [ ] Tablet (768px): layout adaptado
   - [ ] Desktop (1440px): layout completo

6. **Accesibilidad**
   - [ ] Tab navigation funciona en todos los formularios
   - [ ] Focus visible en botones e inputs
   - [ ] Contraste de texto cumple AA

---

## Decisiones de diseno

| Decision | Razon |
|----------|-------|
| Dark theme como default | Premium, reduce fatiga visual en uso prolongado |
| Glass morphism sutil | Profundidad sin distraer, moderno |
| Inter como tipografia | Alta legibilidad, profesional, amplio soporte |
| Badges con colores semanticos | Estado visible de un vistazo |
| Toast en vez de alert | No bloquea la UI, mejor UX |
| Stat chips para metricas | Informacion densa pero escaneable |
| Guide card con pasos | Onboarding visual del modelo Lean |
| Border-left en forms de record | Identificacion rapida de canal (LIVE/ORGANIC/PAID) |
| Sticky table headers | Contexto al hacer scroll en tablas largas |
| Loading spinners | Feedback visual durante fetches |

---

## Antes / Despues

| Aspecto | Antes | Despues |
|---------|-------|---------|
| Tema | Claro basico, fondo blanco | Dark premium con glass |
| Tipografia | system-ui generica | Inter, jerarquia clara |
| Colores | Azul generico | Gradiente brand purple, semanticos |
| Cards | Bordes grises, sombras genericas | Glass morphism, blur, bordes sutiles |
| Badges/Pills | Inline basicos | Badges con colores semanticos y bordes |
| Forms | Sin agrupacion visual | Secciones, field-groups, hints |
| Tablas | Basicas | Sticky headers, zebra, hover, wrapper |
| Notificaciones | `alert()` bloqueante | Toast no-bloqueante con tipos |
| Loading | Texto "..." animado | Spinner CSS animado |
| Modal | Basico blanco | Dark glass con titulo gradiente |
| Responsive | Basico | 3 breakpoints, grids adaptativos |
| Accesibilidad | Minima | AA: focus-visible, aria, roles |
| Design system | CSS duplicado en 4 archivos | 1 archivo centralizado reutilizable |
| Consistencia | Cada pagina diferente | Mismo look en las 4 paginas |

---

## Archivos modificados

| Archivo | Tipo |
|---------|------|
| `static/css/design-system.css` | Nuevo - Design system centralizado |
| `static/index.html` | Modificado - Rediseno completo |
| `static/dashboard.html` | Modificado - Rediseno completo |
| `static/records.html` | Modificado - Rediseno completo |
| `static/stats_dashboard.html` | Modificado - Rediseno completo |
| `docs/UI_UPGRADE.md` | Nuevo - Esta documentacion |
