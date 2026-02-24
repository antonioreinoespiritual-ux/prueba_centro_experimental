import React, { useMemo, useState } from 'react'

const modules = [
  { title: 'Cloud', desc: 'Gestión de bibliotecas y archivos', href: '/cloud' },
  { title: 'Hypotheses', desc: 'Listado y seguimiento de hipótesis', href: '/hypotheses' },
  { title: 'Interviews / Records', desc: 'Revisar records e iteraciones', href: '/static/records.html' },
  { title: 'Dashboard', desc: 'Vista ejecutiva y métricas', href: '/static/dashboard.html' },
  { title: 'Proyectos', desc: 'Gestión de proyectos activos', href: '/static/projects.html' },
  { title: 'Públicos', desc: 'Audiencias y segmentación', href: '/static/publics.html' },
]

const createOptions = [
  { key: 'project', label: 'Crear Proyecto', src: '/static/index_legacy.html?form=experiment' },
  { key: 'campaign', label: 'Crear Campaña', src: '/static/index_legacy.html?form=record-paid' },
  { key: 'hypothesis', label: 'Crear Hipótesis', src: '/static/index_legacy.html?form=experiment' },
  { key: 'client', label: 'Crear Cliente', src: '/static/publics.html' },
  { key: 'template', label: 'Crear Plantilla', src: '/static/chat.html' },
  { key: 'record', label: 'Crear Entrevista / Record', src: '/static/index_legacy.html?form=record-organic' },
]

export function App() {
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedForm, setSelectedForm] = useState(null)

  const currentSrc = useMemo(() => {
    const option = createOptions.find((x) => x.key === selectedForm)
    return option?.src ?? '/static/index_legacy.html?form=experiment'
  }, [selectedForm])

  return (
    <main className="home">
      <header className="hero">
        <div>
          <p className="tag">Centro Experimental</p>
          <h1>Portal principal</h1>
          <p className="subtitle">Home renovado en React + Vite con acceso centralizado a todos los módulos.</p>
        </div>
        <div className="heroActions">
          <button className="btn primary" onClick={() => setCreateOpen(true)}>Crear</button>
          <a className="btn" href="/static/index_legacy.html">Home clásico</a>
        </div>
      </header>

      <section className="grid">
        {modules.map((module) => (
          <a key={module.title} href={module.href} className="card">
            <h2>{module.title}</h2>
            <p>{module.desc}</p>
            <span>Entrar →</span>
          </a>
        ))}
      </section>

      <section className="quickLinks">
        <a href="/static/openclaw.html">Crea hipótesis IA</a>
        <a href="/static/delete_hypotheses.html">Eliminar hipótesis</a>
        <a href="/static/delete_records.html">Eliminar records</a>
        <a href="/static/delete_projects.html">Eliminar proyectos</a>
        <a href="/static/edit_project.html">Editar proyecto</a>
        <a href="/static/edit_record.html?id=2">Editar record</a>
      </section>

      {createOpen && (
        <div className="modalWrap" onClick={() => setCreateOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <h3>Crear</h3>
              <button className="btn" onClick={() => setCreateOpen(false)}>Cerrar</button>
            </div>
            <div className="options">
              {createOptions.map((option) => (
                <button
                  key={option.key}
                  className={selectedForm === option.key ? 'btn primary' : 'btn'}
                  onClick={() => setSelectedForm(option.key)}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {selectedForm && (
              <iframe title={selectedForm} className="frame" src={currentSrc} />
            )}
          </div>
        </div>
      )}
    </main>
  )
}
