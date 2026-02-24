import { useEffect, useMemo, useState } from 'react';

type QuestionType = 'short_text' | 'long_text' | 'multiple_choice' | 'checkbox' | 'scale_1_5';
type Question = { id: string; label: string; type: QuestionType; options?: string[]; required?: boolean };
type InterviewTemplate = { id: number; project_id: number; name: string; description?: string | null; fields_json: { questions: Question[] }; created_at: string };
type InterviewSession = { id: number; template_id: number; project_id: number; hypothesis_id?: number | null; client_id?: number | null; metric_name?: string | null; interviewee_name: string; notes?: string | null; responses_json: Record<string, unknown>; created_at: string };
type Client = { id: number; full_name: string; age?: number | null; email?: string | null; phone?: string | null; country: string; state?: string | null; city?: string | null; nationality?: string | null; gender?: string | null; tags: string[]; notes?: string | null; created_at: string };
type Attachment = { id: number; interview_session_id: number; filename: string; content_type?: string | null; size: number; storage_path: string; created_at: string };
type CloudProject = { id: number; project_name: string };
type Hypothesis = { id: number; experiment_id: number; display_name: string };
type Tab = 'clients' | 'run' | 'templates' | 'sessions';

const API_BASE = localStorage.getItem('ce_api_base') || window.location.origin || 'http://127.0.0.1:8000';
const qt: { label: string; value: QuestionType }[] = [
  { label: 'Texto corto', value: 'short_text' },
  { label: 'Texto largo', value: 'long_text' },
  { label: 'Opción múltiple', value: 'multiple_choice' },
  { label: 'Checkbox', value: 'checkbox' },
  { label: 'Escala 1-5', value: 'scale_1_5' },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { ...init, headers: { ...(init?.headers || {}) } });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

function Badge({ text }: { text: string }) { return <span className="badge">{text}</span>; }

export default function App() {
  const [tab, setTab] = useState<Tab>('clients');
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(''), 3000);
    return () => window.clearTimeout(t);
  }, [toast]);

  return <div className="interviews-app"><header className="topbar"><div><h1>Entrevistas</h1><p>Módulo CRM + entrevistas guiadas.</p></div><div className="actions-row"><a className="btn" href="/">Home</a></div></header><div className="tabs card">{['clients','run','templates','sessions'].map((t)=><button key={t} className={`btn ${tab===t?'primary':''}`} onClick={()=>setTab(t as Tab)}>{t==='clients'?'Clientes':t==='run'?'Realizar entrevista':t==='templates'?'Plantillas':'Entrevistas realizadas'}</button>)}</div>{tab==='clients'&&<ClientsTab onToast={setToast} onRunClient={()=>setTab('run')} />}{tab==='run'&&<RunInterviewTab onToast={setToast} />}{tab==='templates'&&<TemplatesTab onToast={setToast} />}{tab==='sessions'&&<SessionsTab />}{toast && <div className="toast">{toast}</div>}</div>;
}

function ClientsTab({ onToast, onRunClient }: { onToast: (t: string) => void; onRunClient: ()=>void }) {
  const [search, setSearch] = useState(''); const [country, setCountry] = useState('');
  const [clients, setClients] = useState<Client[]>([]); const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false); const [detail, setDetail] = useState<Client | null>(null);
  const [clientInterviews, setClientInterviews] = useState<InterviewSession[]>([]);

  const load = async () => {
    setLoading(true);
    const params = new URLSearchParams(); if (search) params.set('search', search); if (country) params.set('country', country);
    try { setClients(await api<Client[]>(`/clients?${params.toString()}`)); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [search, country]);

  const openDetail = async (c: Client) => { setDetail(c); setClientInterviews(await api<InterviewSession[]>(`/clients/${c.id}/interviews`)); };

  return <section className="card"><div className="section-title"><h2>Clientes</h2><button className="btn primary" onClick={()=>setShowForm(true)}>Crear cliente</button></div><div className="grid2"><input placeholder="Buscar nombre/email/teléfono" value={search} onChange={(e)=>setSearch(e.target.value)} /><input placeholder="Filtrar por país" value={country} onChange={(e)=>setCountry(e.target.value)} /></div>{loading&&<p className="muted">Cargando…</p>}{!loading&&clients.length===0&&<p className="muted">No hay clientes todavía. Crea tu primer cliente.</p>}<div className="list">{clients.map((c)=><article key={c.id} className="item clickable" onClick={()=>openDetail(c)}><div><strong>{c.full_name}</strong><p className="muted">{c.country} · {c.email||'sin email'} · {c.phone||'sin teléfono'}</p></div><Badge text={`#${c.id}`} /></article>)}</div>{showForm&&<ClientFormModal onClose={()=>setShowForm(false)} onCreated={()=>{setShowForm(false); load(); onToast('Cliente creado');}} />}{detail&&<ClientDetailModal client={detail} interviews={clientInterviews} onClose={()=>setDetail(null)} onDeleted={async ()=>{await api(`/clients/${detail.id}`,{method:'DELETE'}); setDetail(null); load(); onToast('Cliente eliminado');}} onRun={()=>{localStorage.setItem('interview_selected_client_id', String(detail.id)); onRunClient();}} />}</section>;
}

function ClientFormModal({ onClose, onCreated }: { onClose: ()=>void; onCreated: ()=>void }) {
  const [form, setForm] = useState({ full_name:'', country:'', email:'', phone:'', notes:'' });
  const [saving, setSaving] = useState(false); const [error, setError] = useState('');
  const submit = async () => { if (!form.full_name.trim() || !form.country.trim()) { setError('Nombre y país son obligatorios'); return; }
    setSaving(true); setError('');
    try { await api('/clients',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...form,tags:[]})}); onCreated(); }
    catch (e) { setError((e as Error).message); } finally { setSaving(false); }
  };
  return <div className="modal-backdrop"><div className="modal card"><h3>Crear cliente</h3><input placeholder="Nombre completo*" value={form.full_name} onChange={(e)=>setForm({...form,full_name:e.target.value})} /><input placeholder="País*" value={form.country} onChange={(e)=>setForm({...form,country:e.target.value})} /><input placeholder="Email" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} /><input placeholder="Teléfono" value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})} /><textarea rows={4} placeholder="Notas" value={form.notes} onChange={(e)=>setForm({...form,notes:e.target.value})} />{error&&<p className="error">{error}</p>}<div className="actions-row"><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" onClick={submit} disabled={saving}>{saving?'Guardando…':'Guardar cliente'}</button></div></div></div>;
}

function ClientDetailModal({ client, interviews, onClose, onDeleted, onRun }: { client: Client; interviews: InterviewSession[]; onClose: ()=>void; onDeleted: ()=>void; onRun: ()=>void }) {
  return <div className="modal-backdrop"><div className="modal card"><div className="section-title"><h3>{client.full_name}</h3><button className="btn" onClick={onClose}>Cerrar</button></div><p className="muted">{client.country} · {client.email||'sin email'} · {client.phone||'sin teléfono'}</p><p>{client.notes || 'Sin notas del cliente.'}</p><div className="section-title"><strong>Entrevistas de este cliente</strong><button className="btn primary" onClick={onRun}>Nueva entrevista para este cliente</button></div>{interviews.length===0?<p className="muted">No tiene entrevistas aún.</p>:<div className="list">{interviews.map((i)=><div key={i.id} className="item"><span>#{i.id} · {new Date(i.created_at).toLocaleString()}</span><Badge text={i.metric_name || 'sin métrica'} /></div>)}</div>}<div className="actions-row"><button className="btn danger" onClick={()=>window.confirm('¿Eliminar cliente?')&&onDeleted()}>Eliminar cliente</button></div></div></div>;
}

function TemplatesTab({ onToast }: { onToast: (t: string)=>void }) {
  const [projectId, setProjectId] = useState(1); const [templates,setTemplates]=useState<InterviewTemplate[]>([]);
  const [editing, setEditing] = useState<InterviewTemplate|null>(null);
  const load = async ()=>setTemplates(await api<InterviewTemplate[]>(`/interviews/projects/${projectId}/templates`));
  useEffect(()=>{load();},[projectId]);
  return <section className="card"><div className="section-title"><h2>Plantillas</h2><div className="actions-row"><input type="number" value={projectId} onChange={(e)=>setProjectId(Number(e.target.value)||1)} /><button className="btn primary" onClick={()=>setEditing({id:0,project_id:projectId,name:'',description:'',fields_json:{questions:[]},created_at:''})}>Crear plantilla</button></div></div>{templates.length===0?<p className="muted">No hay plantillas para este proyecto.</p>:<div className="list">{templates.map((t)=><div className="item" key={t.id}><div><strong>{t.name}</strong><p className="muted">{t.description||'Sin descripción'}</p></div><div className="actions-row"><button className="btn" onClick={()=>setEditing(t)}>Editar</button><button className="btn danger" onClick={async()=>{if(!window.confirm('Eliminar plantilla?'))return; await api(`/interviews/templates/${t.id}`,{method:'DELETE'}); load(); onToast('Plantilla eliminada');}}>Eliminar</button></div></div>)}</div>}{editing&&<TemplateEditor projectId={projectId} initial={editing} onClose={()=>setEditing(null)} onSaved={()=>{setEditing(null);load();onToast('Plantilla guardada');}} />}</section>;
}

function TemplateEditor({ projectId, initial, onClose, onSaved }: { projectId:number; initial:InterviewTemplate; onClose:()=>void; onSaved:()=>void }) {
  const [name,setName]=useState(initial.name||''); const [description,setDescription]=useState(initial.description||''); const [questions,setQuestions]=useState<Question[]>(initial.fields_json.questions||[]);
  const save = async () => {
    const payload={project_id:projectId,name,description,fields_json:{questions}};
    if(initial.id) await api(`/interviews/templates/${initial.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    else await api('/interviews/templates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    onSaved();
  };
  return <div className="modal-backdrop"><div className="modal card"><h3>{initial.id?'Editar':'Nueva'} plantilla</h3><input value={name} placeholder="Nombre" onChange={(e)=>setName(e.target.value)} /><textarea value={description||''} placeholder="Descripción" onChange={(e)=>setDescription(e.target.value)} /><button className="btn" onClick={()=>setQuestions((q)=>[...q,{id:crypto.randomUUID(),label:'',type:'short_text',required:false,options:[]}])}>Agregar pregunta</button><div className="list">{questions.map((q,idx)=><div className="item question" key={q.id}><input value={q.label} placeholder={`Pregunta ${idx+1}`} onChange={(e)=>setQuestions((all)=>all.map((x)=>x.id===q.id?{...x,label:e.target.value}:x))} /><select value={q.type} onChange={(e)=>setQuestions((all)=>all.map((x)=>x.id===q.id?{...x,type:e.target.value as QuestionType,options:[]}:x))}>{qt.map((t)=><option key={t.value} value={t.value}>{t.label}</option>)}</select>{(q.type==='multiple_choice'||q.type==='checkbox')&&<textarea placeholder='Opciones (una por línea)' value={(q.options||[]).join('\n')} onChange={(e)=>setQuestions((all)=>all.map((x)=>x.id===q.id?{...x,options:e.target.value.split('\n').map((n)=>n.trim()).filter(Boolean)}:x))} />}<label className='inline'><input type='checkbox' checked={!!q.required} onChange={(e)=>setQuestions((all)=>all.map((x)=>x.id===q.id?{...x,required:e.target.checked}:x))} />Requerida</label><div className="actions-row"><button className="btn" onClick={()=>idx>0&&setQuestions((all)=>move(all,idx,idx-1))}>↑</button><button className="btn" onClick={()=>idx<questions.length-1&&setQuestions((all)=>move(all,idx,idx+1))}>↓</button><button className="btn danger" onClick={()=>setQuestions((all)=>all.filter((x)=>x.id!==q.id))}>Eliminar</button></div></div>)}</div><div className="actions-row"><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" onClick={save}>Guardar</button></div></div></div>;
}

function RunInterviewTab({ onToast }: { onToast: (t: string)=>void }) {
  const [projects,setProjects]=useState<CloudProject[]>([]); const [hypotheses,setHypotheses]=useState<Hypothesis[]>([]); const [clients,setClients]=useState<Client[]>([]); const [templates,setTemplates]=useState<InterviewTemplate[]>([]);
  const [projectId,setProjectId]=useState<number>(1); const [hypothesisId,setHypothesisId]=useState<number|undefined>(); const [clientId,setClientId]=useState<number|undefined>(); const [templateId,setTemplateId]=useState<number|undefined>();
  const [metricName,setMetricName]=useState(''); const [intervieweeName,setIntervieweeName]=useState(''); const [notes,setNotes]=useState(''); const [responses,setResponses]=useState<Record<string,unknown>>({});
  const [saveState,setSaveState]=useState<'idle'|'saving'|'saved'>('idle'); const [session,setSession]=useState<InterviewSession|null>(null); const [attachments,setAttachments]=useState<Attachment[]>([]);

  const selectedTemplate = useMemo(()=>templates.find((t)=>t.id===templateId),[templates,templateId]);

  useEffect(()=>{(async()=>{try{setProjects(await api<CloudProject[]>('/api/cloud/projects'));}catch{setProjects([]);} setClients(await api<Client[]>('/clients'));})();},[]);
  useEffect(()=>{(async()=>{setTemplates(await api<InterviewTemplate[]>(`/interviews/projects/${projectId}/templates`)); try{setHypotheses(await api<Hypothesis[]>(`/api/cloud/projects/${projectId}/hypotheses`));}catch{setHypotheses([]);} })();},[projectId]);
  useEffect(()=>{ const pre=localStorage.getItem('interview_selected_client_id'); if(pre){ setClientId(Number(pre)); localStorage.removeItem('interview_selected_client_id'); } },[]);

  const persist = async (autosave=false) => {
    if (!projectId || !templateId || !clientId || !intervieweeName.trim()) return;
    setSaveState('saving');
    const payload={project_id:projectId,hypothesis_id:hypothesisId,client_id:clientId,template_id:templateId,metric_name:metricName,interviewee_name:intervieweeName,responses_json:responses,notes};
    try {
      let saved: InterviewSession;
      if (session) saved = await api<InterviewSession>(`/interviews/${session.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      else saved = await api<InterviewSession>('/interviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      setSession(saved); setSaveState('saved'); if(!autosave) onToast('Entrevista guardada');
      if (saved.id) setAttachments(await api<Attachment[]>(`/interviews/${saved.id}/attachments`));
    } catch { setSaveState('idle'); }
  };

  useEffect(()=>{
    const i=window.setInterval(()=>{ if(session || Object.keys(responses).length || notes || intervieweeName){ persist(true);} },15000);
    return ()=>window.clearInterval(i);
  });

  const upload = async (file: File) => {
    if (!session) { onToast('Guarda la entrevista antes de subir archivos'); return; }
    const fd = new FormData(); fd.append('file', file);
    await fetch(`${API_BASE}/interviews/${session.id}/attachments`,{method:'POST',body:fd});
    setAttachments(await api<Attachment[]>(`/interviews/${session.id}/attachments`));
    onToast('Archivo adjuntado');
  };

  return <section className="card"><h2>Realizar entrevista</h2><div className="wizard"><h4>Paso 1 · Contexto</h4><div className='grid2'><select value={projectId} onChange={(e)=>setProjectId(Number(e.target.value)||1)}>{projects.map((p)=><option key={p.id} value={p.id}>{p.project_name}</option>)}</select><select value={hypothesisId||''} onChange={(e)=>setHypothesisId(e.target.value?Number(e.target.value):undefined)}><option value=''>Selecciona hipótesis</option>{hypotheses.map((h)=><option key={h.experiment_id} value={h.experiment_id}>{h.display_name}</option>)}</select></div><input placeholder='Métrica X o variable X' value={metricName} onChange={(e)=>setMetricName(e.target.value)} /><h4>Paso 2 · Cliente</h4><select value={clientId||''} onChange={(e)=>setClientId(e.target.value?Number(e.target.value):undefined)}><option value=''>Selecciona cliente</option>{clients.map((c)=><option key={c.id} value={c.id}>{c.full_name} · {c.country}</option>)}</select><h4>Paso 3 · Plantilla</h4><select value={templateId||''} onChange={(e)=>setTemplateId(e.target.value?Number(e.target.value):undefined)}><option value=''>Selecciona plantilla</option>{templates.map((t)=><option key={t.id} value={t.id}>{t.name}</option>)}</select><h4>Paso 4 · Respuestas</h4><input placeholder='Nombre del entrevistado' value={intervieweeName} onChange={(e)=>setIntervieweeName(e.target.value)} />{selectedTemplate?.fields_json.questions.map((q)=><Field key={q.id} q={q} value={responses[q.id]} onChange={(v)=>setResponses((prev)=>({...prev,[q.id]:v}))} />)}<textarea rows={7} placeholder='Notas libres del entrevistador' value={notes} onChange={(e)=>setNotes(e.target.value)} /><div className='actions-row'><button className='btn primary' onClick={()=>persist(false)}>Guardar entrevista</button><span className='muted'>{saveState==='saving'?'Guardando…':saveState==='saved'?'Guardado':''}</span></div><h4>Paso 5 · Archivos de transcripción</h4><input type='file' accept='.txt,.pdf,.doc,.docx' onChange={(e)=>e.target.files?.[0]&&upload(e.target.files[0])} />{attachments.length===0?<p className='muted'>No hay archivos adjuntos.</p>:<div className='list'>{attachments.map((a)=><div className='item' key={a.id}><div><strong>{a.filename}</strong><p className='muted'>{Math.round(a.size/1024)} KB · {new Date(a.created_at).toLocaleString()}</p></div><button className='btn danger' onClick={async()=>{await api(`/attachments/${a.id}`,{method:'DELETE'}); setAttachments(await api<Attachment[]>(`/interviews/${session!.id}/attachments`));}}>Eliminar</button></div>)}</div>}</div></section>;
}

function Field({ q, value, onChange }: { q: Question; value: unknown; onChange: (v: unknown)=>void }) {
  return <div className="field-block"><label>{q.label} {q.required?'*':''}</label>{q.type==='short_text'&&<input value={(value as string)||''} onChange={(e)=>onChange(e.target.value)} />}{q.type==='long_text'&&<textarea value={(value as string)||''} onChange={(e)=>onChange(e.target.value)} />}{q.type==='multiple_choice'&&<select value={(value as string)||''} onChange={(e)=>onChange(e.target.value)}><option value=''>Selecciona…</option>{(q.options||[]).map((o)=><option key={o} value={o}>{o}</option>)}</select>}{q.type==='checkbox'&&<div className='checkbox-group'>{(q.options||[]).map((o)=>{const arr=Array.isArray(value)?value as string[]:[]; return <label key={o} className='inline'><input type='checkbox' checked={arr.includes(o)} onChange={(e)=>onChange(e.target.checked?[...arr,o]:arr.filter((x)=>x!==o))} />{o}</label>;})}</div>}{q.type==='scale_1_5'&&<input type='range' min={1} max={5} value={Number(value||3)} onChange={(e)=>onChange(Number(e.target.value))} />}</div>;
}

function SessionsTab() {
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  useEffect(()=>{ api<InterviewSession[]>('/interviews?limit=200').then(setSessions).catch(()=>setSessions([])); },[]);
  return <section className='card'><h2>Entrevistas realizadas</h2>{sessions.length===0?<p className='muted'>No hay entrevistas todavía.</p>:<div className='list'>{sessions.map((s)=><div key={s.id} className='item'><div><strong>#{s.id} · {s.interviewee_name}</strong><p className='muted'>Proyecto {s.project_id} · Hipótesis {s.hypothesis_id || '-'} · Cliente {s.client_id || '-'}</p></div><Badge text={new Date(s.created_at).toLocaleDateString()} /></div>)}</div>}</section>;
}

function move<T>(arr: T[], from: number, to: number) { const n=[...arr]; const [x]=n.splice(from,1); n.splice(to,0,x); return n; }
