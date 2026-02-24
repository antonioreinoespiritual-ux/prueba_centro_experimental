const modules=[['Cloud','/cloud','Documentos, bibliotecas y estructura por proyecto.'],['Entrevistas','/interviews','Campañas, clientes, plantillas y entrevistas.'],['Hypotheses','/hypotheses','Gestión y análisis de hipótesis y records.'],['Públicos','/publics-app','Taxonomía de públicos y detalle consolidado.']]
const quick=[['Chat','/static/chat.html'],['Crea hipótesis IA','/static/openclaw.html'],['Dashboard','/static/dashboard.html'],['Lista de proyectos','/static/projects.html'],['Lista de records','/static/records.html'],['Eliminar hipótesis','/static/delete_hypotheses.html',1],['Eliminar records','/static/delete_records.html',1],['Eliminar proyectos','/static/delete_projects.html',1],['Eliminar públicos','/static/delete_publics.html',1]]
const createHint={project:'Usa el modo “Proyecto: Nuevo” dentro del formulario de experimento para crear el proyecto sin cambiar la lógica existente.',hypothesis:'Esta vista reutiliza el formulario original de creación de hipótesis tal como existe hoy.',record:'Esta vista reutiliza los formularios originales de creación de records (organic/live/paid).'}
const app=document.getElementById('app')
function nav(to){history.pushState({},'',to);render()}
window.addEventListener('popstate',render)
function home(){
  app.innerHTML=`<main class='home'><header class='topbar'><div><p class='eyebrow'>Research OS</p><h1>Centro Experimental</h1><p class='muted'>Portal central con acceso a todos los módulos existentes.</p></div><div class='actions'><div class='create-wrap'><button id='createBtn' class='btn primary'>Crear</button><div id='createMenu' class='dropdown' style='display:none'><a href='/create/project' data-nav>Crear Proyecto</a><a href='/create/hypothesis' data-nav>Crear Hipótesis</a><a href='/create/record' data-nav>Crear Record</a></div></div>${quick.map(([l,h,w])=>`<a class='btn ${w?'warn':''}' href='${h}'>${l}</a>`).join('')}</div></header><section class='grid'>${modules.map(([t,h,d])=>`<a class='card' href='${h}'><h2>${t}</h2><p>${d}</p></a>`).join('')}</section></main>`
  document.getElementById('createBtn').onclick=()=>{const m=document.getElementById('createMenu');m.style.display=m.style.display==='none'?'grid':'none'}
  app.querySelectorAll('[data-nav]').forEach(a=>a.onclick=(e)=>{e.preventDefault();nav(a.getAttribute('href'))})
}
function create(type){
  app.innerHTML=`<main class='create-page'><header class='create-head'><div><p class='eyebrow'>Crear</p><h1>Crear ${type==='project'?'Proyecto':type==='hypothesis'?'Hipótesis':'Record'}</h1><p class='muted'>${createHint[type]}</p></div><a class='btn' href='/' data-nav>Volver al Home</a></header><div class='embed-card'><iframe src='/static/index.html#create-${type}' title='create'></iframe></div></main>`
  app.querySelector('[data-nav]').onclick=(e)=>{e.preventDefault();nav('/')}
}
function render(){
  const p=location.pathname
  if(p==='/create/project')return create('project')
  if(p==='/create/hypothesis')return create('hypothesis')
  if(p==='/create/record')return create('record')
  return home()
}
render()
