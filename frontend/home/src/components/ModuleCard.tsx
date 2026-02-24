type Props = {
  title: string;
  description: string;
  href: string;
};

export function ModuleCard({ title, description, href }: Props) {
  return (
    <a className="module-card" href={href}>
      <h2>{title}</h2>
      <p>{description}</p>
      <span>Entrar</span>
    </a>
  );
}
