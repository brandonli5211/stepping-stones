import { STATUS_LABELS, Stone } from "./Stone.jsx";

/** Vertical list of steps: stone, step name and status. steps: [{ name, status }]. */
export function StepList({ steps, numbered = false }) {
  return (
    <ol className="steps">
      {steps.map((step, i) => (
        <li key={i} className={`steps__item steps__item--${step.status}`}>
          <Stone status={step.status} />
          <div>
            {numbered && <span className="muted">Step {i + 1} </span>}
            {step.name}
            {step.status !== "procedure" && <div className="small muted">{STATUS_LABELS[step.status]}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
}
