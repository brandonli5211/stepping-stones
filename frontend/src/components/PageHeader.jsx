import { Link } from "../router.jsx";

/** Back link, big title (with optional leading icon) and subtitle. */
export function PageHeader({ title, subtitle, back, leading }) {
  return (
    <header className="page-header">
      {back && (
        <Link to={back.to} className="button button--pill">
          ← {back.label}
        </Link>
      )}
      <h1>
        {leading}
        {title}
      </h1>
      {subtitle && <p className="muted">{subtitle}</p>}
    </header>
  );
}
