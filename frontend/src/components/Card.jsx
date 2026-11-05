import { Stone } from "./Stone.jsx";

/** White rounded panel; `title` adds a header row. */
export function Card({ title, meta, className = "", children }) {
  return (
    <section className={`card ${className}`}>
      {title && (
        <h2 className="card__title">
          {title} {meta && <span className="muted small">{meta}</span>}
        </h2>
      )}
      {children}
    </section>
  );
}

/** Placeholder / "nothing here" message. */
export function EmptyState({ title, message }) {
  return (
    <div className="empty">
      <Stone status="review" size="lg" label={title} />
      <h3>{title}</h3>
      <p className="muted">{message}</p>
    </div>
  );
}
