import { useEffect, useMemo, useState } from 'react';

type QuestionType = 'short_text' | 'long_text' | 'multiple_choice' | 'checkbox' | 'scale_1_5';
type Question = { id: string; label: string; type: QuestionType; options?: string[]; required?: boolean };
type InterviewTemplate = { id: number; project_id: number; name: string; description?: string | null; fields_json: { questions: Question[] }; created_at: string };
type InterviewSession = { id: number; template_id: number; project_id: number; interviewee_name: string; notes?: string | null; responses_json: Record<string, unknown>; created_at: string };
type View = 'templates' | 'builder' | 'sessions' | 'run';

const API_BASE = localStorage.getItem('ce_api_base') || window.location.origin || 'http://127.0.0.1:8000';
const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: 'Texto corto', value: 'short_text' },
  { label: 'Texto largo', value: 'long_text' },
  { label: 'Opción múltiple', value: 'multiple_choice' },
  { label: 'Checkbox', value: 'checkbox' },
  { label: 'Escala (1-5)', value: 'scale_1_5' },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export default function App() {
  const [projectId, setProjectId] = useState(1);
  const [view, setView] = useState<View>('templates');
  const [templates, setTemplates] = useState<InterviewTemplate[]>([]);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [editingTemplate, setEditingTemplate] = useState<InterviewTemplate | null>(null);
  const [runningTemplate, setRunningTemplate] = useState<InterviewTemplate | null>(null);

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    setError('');
    try { setTemplates(await api<InterviewTemplate[]>(`/interviews/projects/${projectId}/templates`)); }
    catch (e) { setError(`No se pudo cargar plantillas: ${(e as Error).message}`); }
    finally { setLoadingTemplates(false); }
  };
  const loadSessions = async () => {
    setLoadingSessions(true);
    setError('');
    try { setSessions(await api<InterviewSession[]>(`/interviews/projects/${projectId}/sessions`)); }
    catch (e) { setError(`No se pudo cargar entrevistas: ${(e as Error).message}`); }
    finally { setLoadingSessions(false); }
  };

  useEffect(() => { loadTemplates(); loadSessions(); }, [projectId]);
  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(''), 2500);
    return () => window.clearTimeout(t);
  }, [toast]);

  const refreshAll = () => { loadTemplates(); loadSessions(); };

  return (
    <div className="interviews-app">
      <header className="topbar">
        <div><h1>Entrevistas</h1><p>Plantillas y entrevistas por proyecto.</p></div>
        <div className="actions-row"><a className="btn" href="/">Home</a><button className="btn" onClick={refreshAll}>Actualizar</button></div>
      </header>
      <section className="card controls">
        <div className="actions-row wrap">
          <button className="btn" onClick={() => setView('templates')}>Plantillas</button>
          <button className="btn" onClick={() => setView('sessions')}>Entrevistas realizadas</button>
        </div>
        <label>Project ID</label>
        <input type="number" min={1} value={projectId} onChange={(e) => setProjectId(Number(e.target.value) || 1)} />
        {error && <p className="error">{error}</p>}
      </section>

      {view === 'templates' && <TemplatesView templates={templates} loading={loadingTemplates} onCreate={() => { setEditingTemplate(null); setView('builder'); }} onEdit={(t) => { setEditingTemplate(t); setView('builder'); }} onRun={(t) => { setRunningTemplate(t); setView('run'); }} onDelete={async (t) => { if (!window.confirm(`Eliminar "${t.name}"?`)) return; await api(`/interviews/templates/${t.id}`, { method: 'DELETE' }); setToast('Plantilla eliminada'); loadTemplates(); }} />}

      {view === 'builder' && <TemplateBuilder projectId={projectId} initialTemplate={editingTemplate} onCancel={() => setView('templates')} onSaved={() => { setToast('Plantilla guardada'); setView('templates'); loadTemplates(); }} />}

      {view === 'sessions' && <SessionsView sessions={sessions} templates={templates} loading={loadingSessions} onRun={(t) => { setRunningTemplate(t); setView('run'); }} onDelete={async (s) => { if (!window.confirm(`Eliminar entrevista #${s.id}?`)) return; await api(`/interviews/sessions/${s.id}`, { method: 'DELETE' }); setToast('Entrevista eliminada'); loadSessions(); }} />}

      {view === 'run' && runningTemplate && <RunInterviewView projectId={projectId} template={runningTemplate} onBack={() => setView('sessions')} onSaved={() => { setToast('Entrevista guardada'); setView('sessions'); loadSessions(); }} />}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function TemplatesView({ templates, loading, onCreate, onEdit, onRun, onDelete }: { templates: InterviewTemplate[]; loading: boolean; onCreate: () => void; onEdit: (t: InterviewTemplate) => void; onRun: (t: InterviewTemplate) => void; onDelete: (t: InterviewTemplate) => void; }) {
  return <section className="card"><div className="section-title"><h2>Plantillas</h2><button className="btn primary" onClick={onCreate}>Crear plantilla</button></div>{loading && <p className="muted">Cargando…</p>}{!loading && templates.length===0 && <p className="muted">Sin plantillas.</p>}<div className="list">{templates.map((t)=><article key={t.id} className="item"><div><strong>{t.name}</strong><p className="muted">{t.description || 'Sin descripción'}</p></div><div className="actions-row"><button className="btn" onClick={()=>onEdit(t)}>Editar</button><button className="btn" onClick={()=>onRun(t)}>Iniciar</button><button className="btn danger" onClick={()=>onDelete(t)}>Eliminar</button></div></article>)}</div></section>;
}

function TemplateBuilder({ projectId, initialTemplate, onCancel, onSaved }: { projectId: number; initialTemplate: InterviewTemplate | null; onCancel: () => void; onSaved: () => void; }) {
  const [name, setName] = useState(initialTemplate?.name ?? '');
  const [description, setDescription] = useState(initialTemplate?.description ?? '');
  const [questions, setQuestions] = useState<Question[]>(initialTemplate?.fields_json.questions ?? []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const save = async () => {
    setSaving(true); setError('');
    const payload = { project_id: projectId, name, description, fields_json: { questions } };
    try {
      if (initialTemplate) await api(`/interviews/templates/${initialTemplate.id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      else await api('/interviews/templates', { method: 'POST', body: JSON.stringify(payload) });
      onSaved();
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  };

  return <section className="card"><div className="section-title"><h2>{initialTemplate ? 'Editar plantilla' : 'Nueva plantilla'}</h2></div><label>Nombre</label><input value={name} onChange={(e)=>setName(e.target.value)} /><label>Descripción</label><textarea value={description} onChange={(e)=>setDescription(e.target.value)} /><div className="section-title"><h3>Preguntas</h3><button className="btn" onClick={()=>setQuestions((p)=>[...p,{id: crypto.randomUUID(), label:'', type:'short_text', required:false, options:[]}])}>Agregar</button></div>{questions.map((q,idx)=><QuestionEditor key={q.id} question={q} index={idx} onChange={(n)=>setQuestions((all)=>all.map((x)=>x.id===q.id?n:x))} onDelete={()=>setQuestions((all)=>all.filter((x)=>x.id!==q.id))} onMoveUp={()=>idx>0&&setQuestions((all)=>move(all,idx,idx-1))} onMoveDown={()=>idx<questions.length-1&&setQuestions((all)=>move(all,idx,idx+1))} />)}{questions.length===0&&<p className="muted">Agrega al menos una pregunta.</p>}<div className="actions-row"><button className="btn" onClick={onCancel}>Cancelar</button><button className="btn primary" onClick={save} disabled={!name.trim()||questions.length===0||saving}>{saving?'Guardando…':'Guardar plantilla'}</button></div>{error&&<p className="error">{error}</p>}</section>;
}

function QuestionEditor({ question, index, onChange, onDelete, onMoveUp, onMoveDown }: { question: Question; index: number; onChange: (q: Question)=>void; onDelete: ()=>void; onMoveUp: ()=>void; onMoveDown: ()=>void; }) {
  const optionsText = useMemo(() => (question.options || []).join('\n'), [question.options]);
  return <article className="item question"><div className="question-header"><strong>Pregunta {index+1}</strong><div className="actions-row"><button className="btn" onClick={onMoveUp}>↑</button><button className="btn" onClick={onMoveDown}>↓</button><button className="btn danger" onClick={onDelete}>Eliminar</button></div></div><input placeholder="Enunciado" value={question.label} onChange={(e)=>onChange({...question,label:e.target.value})} /><select value={question.type} onChange={(e)=>onChange({...question,type:e.target.value as QuestionType,options:[]})}>{QUESTION_TYPES.map((t)=><option key={t.value} value={t.value}>{t.label}</option>)}</select>{(question.type==='multiple_choice'||question.type==='checkbox')&&<textarea placeholder="Opciones (una por línea)" value={optionsText} onChange={(e)=>onChange({...question,options:e.target.value.split('\n').map((x)=>x.trim()).filter(Boolean)})} />}<label className="inline"><input type="checkbox" checked={Boolean(question.required)} onChange={(e)=>onChange({...question,required:e.target.checked})}/> Requerida</label></article>;
}

function SessionsView({ sessions, templates, loading, onRun, onDelete }: { sessions: InterviewSession[]; templates: InterviewTemplate[]; loading: boolean; onRun: (t: InterviewTemplate)=>void; onDelete: (s: InterviewSession)=>void; }) {
  return <section className="card"><div className="section-title"><h2>Entrevistas realizadas</h2></div><div className="actions-row wrap">{templates.map((t)=><button key={t.id} className="btn" onClick={()=>onRun(t)}>Nueva con: {t.name}</button>)}</div>{loading&&<p className="muted">Cargando…</p>}{!loading&&sessions.length===0&&<p className="muted">Sin entrevistas.</p>}<div className="list">{sessions.map((s)=><article className="item" key={s.id}><div><strong>#{s.id} · {s.interviewee_name}</strong><p className="muted">Template {s.template_id} · {new Date(s.created_at).toLocaleString()}</p></div><button className="btn danger" onClick={()=>onDelete(s)}>Eliminar</button></article>)}</div></section>;
}

function RunInterviewView({ projectId, template, onBack, onSaved }: { projectId: number; template: InterviewTemplate; onBack: ()=>void; onSaved: ()=>void; }) {
  const [intervieweeName, setIntervieweeName] = useState('');
  const [notes, setNotes] = useState('');
  const [responses, setResponses] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const persist = async (isAuto = false) => {
    if (!intervieweeName.trim() && isAuto) return;
    setSaving(true); setError('');
    try {
      await api('/interviews/sessions', { method: 'POST', body: JSON.stringify({ template_id: template.id, project_id: projectId, interviewee_name: intervieweeName || 'Borrador', notes, responses_json: responses }) });
      if (!isAuto) onSaved();
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  };

  useEffect(() => {
    const i = window.setInterval(() => { persist(true); }, 10000);
    return () => window.clearInterval(i);
  });

  const requiredMissing = template.fields_json.questions.filter((q)=>q.required).some((q)=>{
    const v = responses[q.id];
    return !v || (Array.isArray(v) && v.length===0);
  });

  return <section className="card"><div className="section-title"><h2>Ejecutar · {template.name}</h2></div><label>Entrevistado</label><input value={intervieweeName} onChange={(e)=>setIntervieweeName(e.target.value)} />{template.fields_json.questions.map((q)=><FieldRenderer key={q.id} question={q} value={responses[q.id]} onChange={(v)=>setResponses((prev)=>({...prev,[q.id]:v}))} />)}<label>Notas libres</label><textarea rows={6} value={notes} onChange={(e)=>setNotes(e.target.value)} /><div className="actions-row"><button className="btn" onClick={onBack}>Volver</button><button className="btn primary" disabled={saving || !intervieweeName.trim() || requiredMissing} onClick={()=>persist(false)}>{saving?'Guardando…':'Guardar entrevista'}</button></div>{requiredMissing&&<p className="error">Completa preguntas requeridas.</p>}{error&&<p className="error">{error}</p>}</section>;
}

function FieldRenderer({ question, value, onChange }: { question: Question; value: unknown; onChange: (v: unknown)=>void; }) {
  return <div className="field-block"><label>{question.label || 'Pregunta'} {question.required?'*':''}</label>{question.type==='short_text'&&<input value={(value as string)||''} onChange={(e)=>onChange(e.target.value)} />}{question.type==='long_text'&&<textarea value={(value as string)||''} onChange={(e)=>onChange(e.target.value)} />}{question.type==='multiple_choice'&&<select value={(value as string)||''} onChange={(e)=>onChange(e.target.value)}><option value="">Selecciona…</option>{(question.options||[]).map((opt)=><option key={opt} value={opt}>{opt}</option>)}</select>}{question.type==='checkbox'&&<div className="checkbox-group">{(question.options||[]).map((opt)=>{const arr = Array.isArray(value)? value as string[] : []; const checked=arr.includes(opt); return <label key={opt} className="inline"><input type="checkbox" checked={checked} onChange={(e)=>{const next=e.target.checked?[...arr,opt]:arr.filter((i)=>i!==opt); onChange(next);}} />{opt}</label>;})}</div>}{question.type==='scale_1_5'&&<input type="range" min={1} max={5} value={Number(value||3)} onChange={(e)=>onChange(Number(e.target.value))} />}</div>;
}

function move(items: Question[], from: number, to: number) {
  const next = [...items];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}
