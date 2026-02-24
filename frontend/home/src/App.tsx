import { useMemo, useState } from 'react'

type CreateKind = 'project' | 'campaign' | 'hypothesis' | 'client' | 'template' | 'interview' | 'record'

const API_BASE = window.location.origin

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const payload = response.headers.get('content-type')?.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) throw new Error(typeof payload === 'string' ? payload : payload.detail || 'Request failed')
  return payload as T
}

export default function App() {
  const [activeCreate, setActiveCreate] = useState<CreateKind | null>(null)
  const [status, setStatus] = useState<string>('')

  const forms = useMemo(() => ({
    project: { name: '', hypothesis: '', traffic_type: 'organic' },
    campaign: { name: '', project_id: '', status: 'planned' },
    hypothesis: { project_name: '', hypothesis: '', traffic_type: 'paid' },
    client: { full_name: '', country: '', campaign_id: '' },
    template: { name: '', project_id: '', campaign_id: '' },
    interview: { project_id: '', campaign_id: '', template_id: '', interviewee_name: '' },
    record: { experiment_id: '', session_id: '', record_name: '' },
  }), [])

  const [data, setData] = useState(forms)

  const update = (k: CreateKind, key: string, value: string) => setData((old) => ({ ...old, [k]: { ...old[k], [key]: value } }))

  const submit = async (k: CreateKind) => {
    try {
      setStatus('Guardando...')
      if (k === 'project' || k === 'hypothesis') {
        await api('/experiments/', 'POST', {
          project_name: data[k].project_name || data[k].name,
          hypothesis: data[k].hypothesis,
          traffic_type: data[k].traffic_type,
        })
      }
      if (k === 'campaign') {
        await api('/api/campaigns', 'POST', { name: data.campaign.name, project_id: Number(data.campaign.project_id), status: data.campaign.status })
      }
      if (k === 'client') {
        await api('/clients', 'POST', {
          full_name: data.client.full_name,
          country: data.client.country,
          campaign_id: Number(data.client.campaign_id),
          tags: [],
        })
      }
      if (k === 'template') {
        await api('/api/interviews/templates', 'POST', {
          name: data.template.name,
          description: '',
          project_id: Number(data.template.project_id),
          campaign_id: Number(data.template.campaign_id),
          fields_json: { sections: [] },
        })
      }
      if (k === 'interview') {
        await api('/api/interviews', 'POST', {
          project_id: Number(data.interview.project_id),
          campaign_id: Number(data.interview.campaign_id),
          template_id: Number(data.interview.template_id),
          interviewee_name: data.interview.interviewee_name,
          responses_json: {},
        })
      }
      if (k === 'record') {
        await api('/records/', 'POST', {
          experiment_id: Number(data.record.experiment_id),
          session_id: data.record.session_id,
          record_name: data.record.record_name,
        })
      }
      setStatus('✅ Creado correctamente')
      setTimeout(() => setStatus(''), 2500)
      setActiveCreate(null)
    } catch (error) {
      setStatus(`❌ ${error instanceof Error ? error.message : 'Error inesperado'}`)
    }
  }

  return (
    <div className="home">
      <header className="topbar">
        <div>
          <h1>Centro Experimental</h1>
          <p>Portal unificado estilo Cloud</p>
        </div>
        <div className="actions">
          <button className="primary" onClick={() => setActiveCreate('project')}>Crear</button>
          <a href="/cloud">Cloud</a>
          <a href="/interviews">Entrevistas</a>
          <a href="/hypotheses">Hypotheses</a>
        </div>
      </header>

      <section className="cards">
        {[
          ['Cloud', '/cloud', 'Gestión documental y bibliotecas'],
          ['Entrevistas', '/interviews', 'Campañas, plantillas y sesiones'],
          ['Hypotheses', '/hypotheses', 'Hipótesis y validación'],
          ['Públicos', '/publics-app', 'CRM y segmentación'],
          ['Dashboard', '/static/dashboard.html', 'Visión global'],
          ['Chat', '/static/chat.html', 'Asistente'],
        ].map(([name, href, desc]) => (
          <a key={href} className="card" href={href}>
            <h3>{name}</h3>
            <p>{desc}</p>
          </a>
        ))}
      </section>

      <section className="quick-links">
        <a href="/static/edit_project.html">Editar proyecto</a>
        <a href="/static/edit_record.html?id=2">Editar record</a>
        <a href="/static/openclaw.html">Crear hipótesis IA</a>
        <a href="/static/projects.html">Lista de proyectos</a>
        <a href="/static/records.html">Lista de records</a>
        <a href="/static/delete_hypotheses.html">Eliminar hipótesis</a>
        <a href="/static/delete_records.html">Eliminar records</a>
        <a href="/static/delete_projects.html">Eliminar proyectos</a>
        <a href="/static/delete_publics.html">Eliminar públicos</a>
        <button onClick={() => window.location.reload()}>Actualizar listas</button>
      </section>

      {status ? <p className="status">{status}</p> : null}

      {activeCreate ? (
        <div className="overlay" onClick={() => setActiveCreate(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Crear</h2>
            <div className="menu">
              {(['project', 'campaign', 'hypothesis', 'client', 'template', 'interview', 'record'] as CreateKind[]).map((kind) => (
                <button key={kind} className={kind === activeCreate ? 'selected' : ''} onClick={() => setActiveCreate(kind)}>{label(kind)}</button>
              ))}
            </div>
            <div className="form">{renderForm(activeCreate, data, update, () => submit(activeCreate))}</div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function label(kind: CreateKind): string {
  return {
    project: 'Crear Proyecto',
    campaign: 'Crear Campaña',
    hypothesis: 'Crear Hipótesis',
    client: 'Crear Cliente',
    template: 'Crear Plantilla',
    interview: 'Crear Entrevista',
    record: 'Crear Record',
  }[kind]
}

function renderForm(
  kind: CreateKind,
  data: Record<CreateKind, Record<string, string>>,
  update: (k: CreateKind, key: string, value: string) => void,
  submit: () => void,
) {
  const fieldsByKind: Record<CreateKind, string[]> = {
    project: ['name', 'hypothesis', 'traffic_type'],
    campaign: ['name', 'project_id', 'status'],
    hypothesis: ['project_name', 'hypothesis', 'traffic_type'],
    client: ['full_name', 'country', 'campaign_id'],
    template: ['name', 'project_id', 'campaign_id'],
    interview: ['project_id', 'campaign_id', 'template_id', 'interviewee_name'],
    record: ['experiment_id', 'session_id', 'record_name'],
  }

  return (
    <>
      {fieldsByKind[kind].map((field) => (
        <label key={field}>{field}
          <input value={data[kind][field]} onChange={(e) => update(kind, field, e.target.value)} placeholder={field} />
        </label>
      ))}
      <button className="primary" onClick={submit}>{label(kind)}</button>
    </>
  )
}
