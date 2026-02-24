const API_BASE = window.location.origin;
const root = document.getElementById('root');

root.innerHTML = `
<main class="shell">
  <header class="topbar">
    <div><h1>Centro Experimental</h1><p>Home optimizado con experiencia cloud.</p></div>
    <div class="actions"><a href="/cloud">Cloud</a><button id="btnCreate">Crear</button></div>
  </header>
  <section id="panel" class="panel hidden">
    <div class="panel-tabs">
      <button data-tab="project">Crear proyecto</button>
      <button data-tab="hypothesis">Crear hipótesis</button>
      <button data-tab="record">Crear record</button>
    </div>
    <form id="projectForm" class="form-grid">
      <label>Nombre del proyecto<input required name="project_name" /></label>
      <label>Hipótesis inicial<textarea name="hypothesis"></textarea></label>
      <button>Guardar proyecto</button>
    </form>
    <form id="hypothesisForm" class="form-grid hidden">
      <label>Proyecto<input required name="project_name" /></label>
      <label>Tráfico<select name="traffic_type"><option>paid</option><option>organic</option><option>mixed</option><option>live</option></select></label>
      <label>Hipótesis<textarea required name="hypothesis"></textarea></label>
      <button>Guardar hipótesis</button>
    </form>
    <form id="recordForm" class="form-grid hidden">
      <label>ID hipótesis<input required name="experiment_id" type="number" /></label>
      <label>Nombre record<input required name="session_id" /></label>
      <button>Guardar record</button>
    </form>
  </section>
  <p id="message" class="message"></p>
</main>`;

const panel = document.getElementById('panel');
const forms = { project: document.getElementById('projectForm'), hypothesis: document.getElementById('hypothesisForm'), record: document.getElementById('recordForm') };

document.getElementById('btnCreate').onclick = () => panel.classList.toggle('hidden');
document.querySelectorAll('[data-tab]').forEach((btn) => {
  btn.addEventListener('click', () => {
    Object.values(forms).forEach((form) => form.classList.add('hidden'));
    forms[btn.dataset.tab].classList.remove('hidden');
  });
});

async function send(path, payload) {
  const r = await fetch(`${API_BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!r.ok) throw new Error('No se pudo crear');
  document.getElementById('message').textContent = 'Creado correctamente';
}
forms.project.onsubmit = async (e) => { e.preventDefault(); const f = new FormData(forms.project); await send('/experiments/', { project_name: f.get('project_name'), hypothesis: f.get('hypothesis') || `Hipótesis inicial`, traffic_type: 'mixed' }); };
forms.hypothesis.onsubmit = async (e) => { e.preventDefault(); const f = new FormData(forms.hypothesis); await send('/experiments/', Object.fromEntries(f.entries())); };
forms.record.onsubmit = async (e) => { e.preventDefault(); const f = new FormData(forms.record); await send('/records/', { experiment_id: Number(f.get('experiment_id')), session_id: f.get('session_id'), record_name: f.get('session_id') }); };
