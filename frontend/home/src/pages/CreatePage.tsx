import { Link } from 'react-router-dom'

type Props = {
  title: string
  anchor: 'project' | 'hypothesis' | 'record'
}

const sectionHint = {
  project: 'Usa el modo “Proyecto: Nuevo” dentro del formulario de experimento para crear el proyecto sin cambiar la lógica existente.',
  hypothesis: 'Esta vista reutiliza el formulario original de creación de hipótesis tal como existe hoy.',
  record: 'Esta vista reutiliza los formularios originales de creación de records (organic/live/paid).',
}

export function CreatePage({ title, anchor }: Props) {
  return (
    <main className="create-page">
      <header className="create-head">
        <div>
          <p className="eyebrow">Crear</p>
          <h1>{title}</h1>
          <p className="muted">{sectionHint[anchor]}</p>
        </div>
        <Link to="/" className="btn">Volver al Home</Link>
      </header>

      <div className="embed-card">
        <iframe title={title} src={`/static/index.html#create-${anchor}`} />
      </div>
    </main>
  )
}
