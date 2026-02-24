import { FormEvent, useEffect, useMemo, useState } from 'react';

type Experiment = { id: number; project_name: string; hypothesis: string };
type CreateType = 'record' | 'hypothesis' | 'project';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? `Error ${response.status}`);
  }
  return (await response.json()) as T;
}

export function App() {
  const [createOpen, setCreateOpen] = useState(false);
  const [createType, setCreateType] = useState<CreateType>('project');
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [message, setMessage] = useState('');

  const [projectName, setProjectName] = useState('');
  const [projectHypothesis, setProjectHypothesis] = useState('');

  const [hypothesisProjectName, setHypothesisProjectName] = useState('');
  const [hypothesisText, setHypothesisText] = useState('');
  const [hypothesisTraffic, setHypothesisTraffic] = useState<'paid' | 'organic' | 'mixed' | 'live'>('paid');

  const [recordExperimentId, setRecordExperimentId] = useState<number | ''>('');
  const [recordName, setRecordName] = useState('');

  useEffect(() => {
    request<Experiment[]>('/experiments/')
      .then((data) => {
        setExperiments(data);
        if (data[0]) {
          setRecordExperimentId(data[0].id);
          setHypothesisProjectName(data[0].project_name);
        }
      })
      .catch(() => setMessage('No se pudieron cargar hipótesis aún.'));
  }, []);

  const uniqueProjects = useMemo(() => Array.from(new Set(experiments.map((e) => e.project_name))), [experiments]);

  const createProject = async (event: FormEvent) => {
    event.preventDefault();
    const hypothesis = projectHypothesis.trim() || `Hipótesis inicial para ${projectName.trim()}`;
    const created = await request<Experiment>('/experiments/', {
      method: 'POST',
      body: JSON.stringify({
        project_name: projectName.trim(),
        hypothesis,
        traffic_type: 'mixed',
      }),
    });
    setExperiments((prev) => [created, ...prev]);
    setProjectName('');
    setProjectHypothesis('');
    setMessage('Proyecto creado y listo para trabajar.');
  };

  const createHypothesis = async (event: FormEvent) => {
    event.preventDefault();
    const created = await request<Experiment>('/experiments/', {
      method: 'POST',
      body: JSON.stringify({
        project_name: hypothesisProjectName.trim(),
        hypothesis: hypothesisText.trim(),
        traffic_type: hypothesisTraffic,
      }),
    });
    setExperiments((prev) => [created, ...prev]);
    setHypothesisText('');
    setMessage('Hipótesis creada correctamente.');
  };

  const createRecord = async (event: FormEvent) => {
    event.preventDefault();
    if (!recordExperimentId) return;
    await request('/records/', {
      method: 'POST',
      body: JSON.stringify({
        experiment_id: recordExperimentId,
        session_id: recordName.trim(),
        record_name: recordName.trim(),
      }),
    });
    setRecordName('');
    setMessage('Record creado correctamente.');
  };

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>Centro Experimental</h1>
          <p>Frontend optimizado en React + Vite, estilo Cloud.</p>
        </div>
        <div className="actions">
          <a href="/cloud">Cloud</a>
          <a href="/static/dashboard.html">Dashboard</a>
          <button onClick={() => setCreateOpen((prev) => !prev)}>Crear</button>
        </div>
      </header>

      {createOpen && (
        <section className="panel">
          <div className="panel-tabs">
            <button className={createType === 'project' ? 'active' : ''} onClick={() => setCreateType('project')}>Crear proyecto</button>
            <button className={createType === 'hypothesis' ? 'active' : ''} onClick={() => setCreateType('hypothesis')}>Crear hipótesis</button>
            <button className={createType === 'record' ? 'active' : ''} onClick={() => setCreateType('record')}>Crear record</button>
          </div>

          {createType === 'project' && (
            <form onSubmit={createProject} className="form-grid">
              <label>Nombre del proyecto
                <input required value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Growth Q2" />
              </label>
              <label>Hipótesis inicial (opcional)
                <textarea value={projectHypothesis} onChange={(e) => setProjectHypothesis(e.target.value)} placeholder="Si mejoramos X entonces crecerá Y" />
              </label>
              <button type="submit">Guardar proyecto</button>
            </form>
          )}

          {createType === 'hypothesis' && (
            <form onSubmit={createHypothesis} className="form-grid">
              <label>Proyecto
                <input list="project-options" required value={hypothesisProjectName} onChange={(e) => setHypothesisProjectName(e.target.value)} placeholder="Proyecto existente o nuevo" />
                <datalist id="project-options">
                  {uniqueProjects.map((project) => <option key={project} value={project} />)}
                </datalist>
              </label>
              <label>Tipo de tráfico
                <select value={hypothesisTraffic} onChange={(e) => setHypothesisTraffic(e.target.value as 'paid' | 'organic' | 'mixed' | 'live')}>
                  <option value="paid">Paid</option>
                  <option value="organic">Organic</option>
                  <option value="mixed">Mixed</option>
                  <option value="live">Live</option>
                </select>
              </label>
              <label className="full">Hipótesis
                <textarea required value={hypothesisText} onChange={(e) => setHypothesisText(e.target.value)} />
              </label>
              <button type="submit">Guardar hipótesis</button>
            </form>
          )}

          {createType === 'record' && (
            <form onSubmit={createRecord} className="form-grid">
              <label>Hipótesis
                <select value={recordExperimentId} onChange={(e) => setRecordExperimentId(Number(e.target.value))} required>
                  {experiments.map((experiment) => (
                    <option key={experiment.id} value={experiment.id}>
                      #{experiment.id} · {experiment.project_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>Nombre del record
                <input required value={recordName} onChange={(e) => setRecordName(e.target.value)} placeholder="R1 Hook A" />
              </label>
              <button type="submit">Guardar record</button>
            </form>
          )}
        </section>
      )}

      {message && <p className="message">{message}</p>}
    </main>
  );
}
