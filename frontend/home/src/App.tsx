import { ModuleCard } from './components/ModuleCard';

const modules = [
  { title: 'Cloud', description: 'Bibliotecas, rutas y archivos por proyecto.', href: '/cloud' },
  { title: 'Hypotheses', description: 'Seguimiento de hipótesis y records.', href: '/hypotheses' },
  { title: 'Entrevistas', description: 'Campañas, clientes, plantillas y sesiones.', href: '/interviews' },
  { title: 'Públicos', description: 'Gestión de segmentos y detalle histórico.', href: '/publics-app' },
  { title: 'Dashboard', description: 'Resumen operativo de resultados.', href: '/static/dashboard.html' },
  { title: 'Chat', description: 'Asistencia y análisis conversacional.', href: '/static/chat.html' },
];

export default function App() {
  return (
    <div className="home-shell">
      <header className="home-topbar">
        <div>
          <p className="home-eyebrow">Research OS</p>
          <h1>Centro Experimental</h1>
          <p className="home-subtitle">Suite unificada con experiencia visual Cloud.</p>
        </div>
        <div className="home-actions">
          <a href="/static/index.html" className="btn secondary">Home legacy</a>
          <a href="/cloud" className="btn primary">Abrir Cloud</a>
        </div>
      </header>

      <section className="module-grid" aria-label="Módulos principales">
        {modules.map((item) => (
          <ModuleCard key={item.title} {...item} />
        ))}
      </section>
    </div>
  );
}
