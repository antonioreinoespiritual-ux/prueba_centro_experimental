import { useEffect, useMemo, useState } from 'react'

const moduleCards = [
  { title: 'Cloud', description: 'Workspace principal estilo Cloud.', href: '/cloud' },
  { title: 'Entrevistas / Records', description: 'Gestión de ejecución y registros.', href: '/static/records.html' },
  { title: 'Hipótesis', description: 'Lista y seguimiento de hipótesis.', href: '/static/hypotheses.html' },
  { title: 'Dashboard', description: 'KPIs y vistas generales.', href: '/static/dashboard.html' },
]

const quickLinks = [
  ['Chat', '/static/chat.html'],
  ['Crea hipótesis IA', '/static/openclaw.html'],
  ['Lista de proyectos', '/static/projects.html'],
  ['Lista de records', '/static/records.html'],
  ['Lista de hipotesis', '/static/hypotheses.html'],
  ['Públicos', '/static/publics.html'],
  ['Eliminar hipotesis', '/static/delete_hypotheses.html'],
  ['Eliminar records', '/static/delete_records.html'],
  ['Eliminar proyectos', '/static/delete_projects.html'],
]

const createOptions = [
  { key: 'project', label: 'Crear Proyecto', target: 'hypothesis' },
  { key: 'campaign', label: 'Crear Campaña', target: 'paid' },
  { key: 'hypothesis', label: 'Crear Hipótesis', target: 'hypothesis' },
  { key: 'client', label: 'Crear Cliente', target: 'publics' },
  { key: 'template', label: 'Crear Plantilla', target: 'guide' },
  { key: 'record', label: 'Crear Entrevista / Record', target: 'live' },
]

export default function App() {
  const [legacyHtml, setLegacyHtml] = useState('')
  const [createOpen, setCreateOpen] = useState(false)

  useEffect(() => {
    fetch('/static/home/legacy-home-content.html').then((r) => r.text()).then(setLegacyHtml)
  }, [])

  useEffect(() => {
    if (!legacyHtml || document.getElementById('legacy-home-script')) return
    const script = document.createElement('script')
    script.id = 'legacy-home-script'
    script.src = '/static/home/legacy-home.js'
    document.body.appendChild(script)
  }, [legacyHtml])

  const targetMap = useMemo(() => ({
    hypothesis: '.card.fade-in[aria-label="Formulario crear experimento"]',
    live: '.record-form--live',
    organic: '.record-form--organic',
    paid: '.record-form--paid',
    publics: 'a[href="/static/publics.html"]',
    guide: '.guide-card',
  }), [])

  const showForm = (target) => {
    const forms = [
      '.card.fade-in[aria-label="Formulario crear experimento"]',
      '.record-form--live',
      '.record-form--organic',
      '.record-form--paid',
    ]
    forms.forEach((sel) => {
      const el = document.querySelector(sel)
      if (el) el.style.display = 'none'
    })
    const el = document.querySelector(targetMap[target])
    if (el && el.tagName !== 'A') {
      el.style.display = 'block'
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    if (target === 'publics') {
      window.location.href = '/static/publics.html'
    }
    setCreateOpen(false)
  }

  return (
    <div className="home-shell">
      <header className="hero">
        <div>
          <h1>Centro Experimental</h1>
          <p>Home renovado con experiencia consistente al estilo Cloud.</p>
        </div>
        <div className="hero-actions">
          <button className="primary" onClick={() => setCreateOpen((v) => !v)}>Crear</button>
          <button className="secondary" onClick={() => document.getElementById('btnRefresh')?.click()}>Actualizar listas</button>
        </div>
      </header>

      {createOpen && (
        <div className="create-menu">
          {createOptions.map((opt) => (
            <button key={opt.key} onClick={() => showForm(opt.target)}>{opt.label}</button>
          ))}
        </div>
      )}

      <section className="cards">
        {moduleCards.map((card) => (
          <a key={card.title} className="card" href={card.href}>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
          </a>
        ))}
      </section>

      <section className="quick-links">
        {quickLinks.map(([label, href]) => <a key={label} href={href}>{label}</a>)}
      </section>

      <section id="legacy-home" dangerouslySetInnerHTML={{ __html: legacyHtml }} />
    </div>
  )
}
