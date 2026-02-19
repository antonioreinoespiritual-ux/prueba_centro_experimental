import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

type QuestionType = 'short_text' | 'long_text' | 'multiple_choice' | 'checkbox' | 'scale_1_5';

type Question = {
  id: string;
  label: string;
  type: QuestionType;
  options?: string[];
  required?: boolean;
};

type InterviewTemplate = {
  id: number;
  project_id: number;
  name: string;
  description?: string | null;
  fields_json: { questions: Question[] };
  created_at: string;
};

type InterviewSession = {
  id: number;
  template_id: number;
  project_id: number;
  interviewee_name: string;
  notes?: string | null;
  responses_json: Record<string, unknown>;
  created_at: string;
};

type View = 'templates' | 'builder' | 'sessions' | 'run';

const API_BASE = localStorage.getItem('ce_api_base') || window.location.origin || 'http://127.0.0.1:8000';

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: 'Texto corto', value: 'short_text' },
  { label: 'Texto largo', value: 'long_text' },
  { label: 'Opción múltiple', value: 'multiple_choice' },
  { label: 'Checkbox', value: 'checkbox' },
  { label: 'Escala (1-5)', value: 'scale_1_5' },
];

export default function App() {
  const [projectId, setProjectId] = useState<number>(1);
  const [view, setView] = useState<View>('templates');
  const [toast, setToast] = useState<string>('');
  const [editingTemplate, setEditingTemplate] = useState<InterviewTemplate | null>(null);
  const [runningTemplate, setRunningTemplate] = useState<InterviewTemplate | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(''), 2800);
    return () => window.clearTimeout(t);
  }, [toast]);

  const templatesQuery = useQuery({
    queryKey: ['interview-templates', projectId],
    queryFn: () => api<InterviewTemplate[]>(`/interviews/projects/${projectId}/templates`),
  });

  const sessionsQuery = useQuery({
    queryKey: ['interview-sessions', projectId],
    queryFn: () => api<InterviewSession[]>(`/interviews/projects/${projectId}/sessions`),
  });

  const removeTemplateMutation = useMutation({
    mutationFn: (templateId: number) => api<{ ok: boolean }>(`/interviews/templates/${templateId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-templates', projectId] });
      setToast('Plantilla eliminada.');
    },
  });

  const removeSessionMutation = useMutation({
    mutationFn: (sessionId: number) => api<{ ok: boolean }>(`/interviews/sessions/${sessionId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-sessions', projectId] });
      setToast('Entrevista eliminada.');
    },
  });

  return (
    <div className="interviews-app">
      <header className="topbar">
        <div>
          <h1>Entrevistas</h1>
          <p>Módulo de plantillas y entrevistas realizadas.</p>
        </div>
        <div className="actions-row">
          <a className="btn" href="/">Home</a>
          <button className="btn" onClick={() => setView('templates')}>Plantillas</button>
          <button className="btn" onClick={() => setView('sessions')}>Entrevistas realizadas</button>
        </div>
      </header>

      <section className="card controls">
        <label>Project ID</label>
        <input type="number" min={1} value={projectId} onChange={(e) => setProjectId(Number(e.target.value) || 1)} />
      </section>

      {view === 'templates' && (
        <TemplatesView
          templates={templatesQuery.data ?? []}
          loading={templatesQuery.isLoading}
          onCreate={() => {
            setEditingTemplate(null);
            setView('builder');
          }}
          onEdit={(item) => {
            setEditingTemplate(item);
            setView('builder');
          }}
          onRun={(item) => {
            setRunningTemplate(item);
            setView('run');
          }}
          onDelete={(item) => {
            if (window.confirm(`Eliminar plantilla "${item.name}"?`)) removeTemplateMutation.mutate(item.id);
          }}
        />
      )}

      {view === 'builder' && (
        <TemplateBuilder
          projectId={projectId}
          initialTemplate={editingTemplate}
          onCancel={() => setView('templates')}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['interview-templates', projectId] });
            setView('templates');
            setToast('Plantilla guardada.');
          }}
        />
      )}

      {view === 'sessions' && (
        <SessionsView
          sessions={sessionsQuery.data ?? []}
          loading={sessionsQuery.isLoading}
          templates={templatesQuery.data ?? []}
          onRun={(template) => {
            setRunningTemplate(template);
            setView('run');
          }}
          onDelete={(item) => {
            if (window.confirm(`Eliminar entrevista #${item.id}?`)) removeSessionMutation.mutate(item.id);
          }}
        />
      )}

      {view === 'run' && runningTemplate && (
        <RunInterviewView
          projectId={projectId}
          template={runningTemplate}
          onBack={() => setView('sessions')}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['interview-sessions', projectId] });
            setToast('Entrevista guardada.');
            setView('sessions');
          }}
        />
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function TemplatesView({ templates, loading, onCreate, onEdit, onDelete, onRun }: {
  templates: InterviewTemplate[];
  loading: boolean;
  onCreate: () => void;
  onEdit: (item: InterviewTemplate) => void;
  onDelete: (item: InterviewTemplate) => void;
  onRun: (item: InterviewTemplate) => void;
}) {
  return (
    <section className="card">
      <div className="section-title">
        <h2>Plantillas</h2>
        <button className="btn primary" onClick={onCreate}>Crear plantilla</button>
      </div>
      {loading && <p className="muted">Cargando plantillas…</p>}
      {!loading && templates.length === 0 && <p className="muted">Aún no hay plantillas para este proyecto.</p>}
      <div className="list">
        {templates.map((t) => (
          <article className="item" key={t.id}>
            <div>
              <strong>{t.name}</strong>
              <p className="muted">{t.description || 'Sin descripción'}</p>
            </div>
            <div className="actions-row">
              <button className="btn" onClick={() => onEdit(t)}>Editar</button>
              <button className="btn" onClick={() => onRun(t)}>Iniciar</button>
              <button className="btn danger" onClick={() => onDelete(t)}>Eliminar</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function TemplateBuilder({ projectId, initialTemplate, onCancel, onSaved }: {
  projectId: number;
  initialTemplate: InterviewTemplate | null;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(initialTemplate?.name ?? '');
  const [description, setDescription] = useState(initialTemplate?.description ?? '');
  const [questions, setQuestions] = useState<Question[]>(initialTemplate?.fields_json.questions ?? []);

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        project_id: projectId,
        name,
        description,
        fields_json: { questions },
      };
      if (initialTemplate) {
        return api<InterviewTemplate>(`/interviews/templates/${initialTemplate.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
      }
      return api<InterviewTemplate>('/interviews/templates', { method: 'POST', body: JSON.stringify(payload) });
    },
    onSuccess: onSaved,
  });

  const addQuestion = () => {
    setQuestions((prev) => [...prev, { id: crypto.randomUUID(), label: '', type: 'short_text', required: false, options: [] }]);
  };

  return (
    <section className="card">
      <div className="section-title"><h2>{initialTemplate ? 'Editar plantilla' : 'Nueva plantilla'}</h2></div>
      <label>Nombre</label>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <label>Descripción</label>
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      <div className="section-title">
        <h3>Preguntas</h3>
        <button className="btn" onClick={addQuestion}>Agregar pregunta</button>
      </div>
      {questions.length === 0 && <p className="muted">No hay preguntas, agrega al menos una.</p>}
      <div className="list">
        {questions.map((q, idx) => (
          <QuestionEditor key={q.id} question={q} index={idx} onChange={(next) => setQuestions((all) => all.map((item) => item.id === q.id ? next : item))}
            onDelete={() => setQuestions((all) => all.filter((item) => item.id !== q.id))}
            onMoveUp={() => idx > 0 && setQuestions((all) => moveQuestion(all, idx, idx - 1))}
            onMoveDown={() => idx < questions.length - 1 && setQuestions((all) => moveQuestion(all, idx, idx + 1))}
          />
        ))}
      </div>
      <div className="actions-row">
        <button className="btn" onClick={onCancel}>Cancelar</button>
        <button className="btn primary" disabled={!name.trim() || questions.length === 0 || saveMutation.isPending} onClick={() => saveMutation.mutate()}>
          {saveMutation.isPending ? 'Guardando…' : 'Guardar plantilla'}
        </button>
      </div>
      {saveMutation.isError && <p className="error">No se pudo guardar la plantilla.</p>}
    </section>
  );
}

function QuestionEditor({ question, index, onChange, onDelete, onMoveUp, onMoveDown }: {
  question: Question;
  index: number;
  onChange: (q: Question) => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}) {
  const optionsText = useMemo(() => (question.options ?? []).join('\n'), [question.options]);
  return (
    <article className="item question">
      <div className="question-header">
        <strong>Pregunta {index + 1}</strong>
        <div className="actions-row">
          <button className="btn" onClick={onMoveUp}>↑</button>
          <button className="btn" onClick={onMoveDown}>↓</button>
          <button className="btn danger" onClick={onDelete}>Eliminar</button>
        </div>
      </div>
      <input placeholder="Etiqueta de pregunta" value={question.label} onChange={(e) => onChange({ ...question, label: e.target.value })} />
      <select value={question.type} onChange={(e) => onChange({ ...question, type: e.target.value as QuestionType, options: [] })}>
        {QUESTION_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
      </select>
      {(question.type === 'multiple_choice' || question.type === 'checkbox') && (
        <textarea
          placeholder="Opciones (una por línea)"
          value={optionsText}
          onChange={(e) => onChange({ ...question, options: e.target.value.split('\n').map((x) => x.trim()).filter(Boolean) })}
        />
      )}
      <label className="inline">
        <input type="checkbox" checked={Boolean(question.required)} onChange={(e) => onChange({ ...question, required: e.target.checked })} /> Requerida
      </label>
    </article>
  );
}

function SessionsView({ sessions, templates, loading, onRun, onDelete }: {
  sessions: InterviewSession[];
  templates: InterviewTemplate[];
  loading: boolean;
  onRun: (template: InterviewTemplate) => void;
  onDelete: (session: InterviewSession) => void;
}) {
  return (
    <section className="card">
      <div className="section-title"><h2>Entrevistas realizadas</h2></div>
      <div className="actions-row wrap">
        {templates.map((t) => <button key={t.id} className="btn" onClick={() => onRun(t)}>Nueva con: {t.name}</button>)}
      </div>
      {loading && <p className="muted">Cargando entrevistas…</p>}
      {!loading && sessions.length === 0 && <p className="muted">Aún no hay entrevistas para este proyecto.</p>}
      <div className="list">
        {sessions.map((s) => (
          <article className="item" key={s.id}>
            <div>
              <strong>#{s.id} · {s.interviewee_name}</strong>
              <p className="muted">Template {s.template_id} · {new Date(s.created_at).toLocaleString()}</p>
            </div>
            <button className="btn danger" onClick={() => onDelete(s)}>Eliminar</button>
          </article>
        ))}
      </div>
    </section>
  );
}

function RunInterviewView({ projectId, template, onBack, onSaved }: {
  projectId: number;
  template: InterviewTemplate;
  onBack: () => void;
  onSaved: () => void;
}) {
  const [intervieweeName, setIntervieweeName] = useState('');
  const [notes, setNotes] = useState('');
  const [responses, setResponses] = useState<Record<string, unknown>>({});

  const saveMutation = useMutation({
    mutationFn: (isDraft: boolean) => api<InterviewSession>('/interviews/sessions', {
      method: 'POST',
      body: JSON.stringify({
        template_id: template.id,
        project_id: projectId,
        interviewee_name: intervieweeName || (isDraft ? 'Borrador' : ''),
        notes,
        responses_json: responses,
      }),
    }),
    onSuccess: onSaved,
  });

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (!intervieweeName.trim()) return;
      saveMutation.mutate(true);
    }, 10000);
    return () => window.clearInterval(interval);
  }, [intervieweeName, notes, responses]);

  const requiredMissing = template.fields_json.questions
    .filter((q) => q.required)
    .some((q) => !responses[q.id] || (Array.isArray(responses[q.id]) && (responses[q.id] as unknown[]).length === 0));

  return (
    <section className="card">
      <div className="section-title">
        <h2>Ejecutar entrevista · {template.name}</h2>
      </div>
      <label>Nombre de entrevistado</label>
      <input value={intervieweeName} onChange={(e) => setIntervieweeName(e.target.value)} />
      {template.fields_json.questions.map((q) => (
        <FieldRenderer key={q.id} question={q} value={responses[q.id]} onChange={(value) => setResponses((prev) => ({ ...prev, [q.id]: value }))} />
      ))}
      <label>Notas libres</label>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={6} />
      <div className="actions-row">
        <button className="btn" onClick={onBack}>Volver</button>
        <button className="btn primary" disabled={saveMutation.isPending || !intervieweeName.trim() || requiredMissing} onClick={() => saveMutation.mutate(false)}>
          {saveMutation.isPending ? 'Guardando…' : 'Guardar entrevista'}
        </button>
      </div>
      {requiredMissing && <p className="error">Completa las preguntas requeridas antes de guardar.</p>}
      {saveMutation.isError && <p className="error">No se pudo guardar la entrevista.</p>}
    </section>
  );
}

function FieldRenderer({ question, value, onChange }: {
  question: Question;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  return (
    <div className="field-block">
      <label>{question.label || 'Pregunta sin título'} {question.required ? '*' : ''}</label>
      {question.type === 'short_text' && <input value={(value as string) || ''} onChange={(e) => onChange(e.target.value)} />}
      {question.type === 'long_text' && <textarea value={(value as string) || ''} onChange={(e) => onChange(e.target.value)} />}
      {question.type === 'multiple_choice' && (
        <select value={(value as string) || ''} onChange={(e) => onChange(e.target.value)}>
          <option value="">Selecciona…</option>
          {(question.options || []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      )}
      {question.type === 'checkbox' && (
        <div className="checkbox-group">
          {(question.options || []).map((opt) => {
            const arr = Array.isArray(value) ? (value as string[]) : [];
            const checked = arr.includes(opt);
            return (
              <label key={opt} className="inline">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => {
                    const next = e.target.checked ? [...arr, opt] : arr.filter((item) => item !== opt);
                    onChange(next);
                  }}
                />
                {opt}
              </label>
            );
          })}
        </div>
      )}
      {question.type === 'scale_1_5' && (
        <input type="range" min={1} max={5} value={Number(value || 3)} onChange={(e) => onChange(Number(e.target.value))} />
      )}
    </div>
  );
}

function moveQuestion(items: Question[], from: number, to: number) {
  const next = [...items];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}
