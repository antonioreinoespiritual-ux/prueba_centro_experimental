import { Link, Route, Routes } from 'react-router-dom'
import { useState } from 'react'
import { CreatePage } from './pages/CreatePage'

const modules = [
  { title: 'Cloud', href: '/cloud', desc: 'Documentos, bibliotecas y estructura por proyecto.' },
  { title: 'Entrevistas', href: '/interviews', desc: 'Campañas, clientes, plantillas y entrevistas.' },
  { title: 'Hypotheses', href: '/hypotheses', desc: 'Gestión y análisis de hipótesis y records.' },
  { title: 'Públicos', href: '/publics-app', desc: 'Taxonomía de públicos y detalle consolidado.' },
]

const quickLinks = [
  { label: 'Chat', href: '/static/chat.html' },
  { label: 'Crea hipótesis IA', href: '/static/openclaw.html' },
  { label: 'Dashboard', href: '/static/dashboard.html' },
  { label: 'Lista de proyectos', href: '/static/projects.html' },
  { label: 'Lista de records', href: '/static/records.html' },
  { label: 'Eliminar hipótesis', href: '/static/delete_hypotheses.html', warning: true },
  { label: 'Eliminar records', href: '/static/delete_records.html', warning: true },
  { label: 'Eliminar proyectos', href: '/static/delete_projects.html', warning: true },
  { label: 'Eliminar públicos', href: '/static/delete_publics.html', warning: true },
]

function Home() {
  const [open, setOpen] = useState(false)
  return (
    <main className="home">
      <header className="topbar">
        <div>
          <p className="eyebrow">Research OS</p>
          <h1>Centro Experimental</h1>
          <p className="muted">Portal central con acceso a todos los módulos existentes.</p>
        </div>
        <div className="actions">
          <div className="create-wrap">
            <button className="btn primary" onClick={() => setOpen((v) => !v)}>Crear</button>
            {open && (
              <div className="dropdown">
                <Link to="/create/project">Crear Proyecto</Link>
                <Link to="/create/hypothesis">Crear Hipótesis</Link>
                <Link to="/create/record">Crear Record</Link>
              </div>
            )}
          </div>
          {quickLinks.map((link) => (
            <a key={link.label} className={`btn ${link.warning ? 'warn' : ''}`} href={link.href}>{link.label}</a>
          ))}
        </div>
      </header>

      <section className="grid">
        {modules.map((module) => (
          <a key={module.title} className="card" href={module.href}>
            <h2>{module.title}</h2>
            <p>{module.desc}</p>
          </a>
        ))}
      </section>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/create/project" element={<CreatePage title="Crear Proyecto" anchor="project" />} />
      <Route path="/create/hypothesis" element={<CreatePage title="Crear Hipótesis" anchor="hypothesis" />} />
      <Route path="/create/record" element={<CreatePage title="Crear Record" anchor="record" />} />
    </Routes>
  )
}
