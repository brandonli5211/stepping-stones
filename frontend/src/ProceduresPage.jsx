import { useEffect, useMemo, useState } from "react";
import { fetchProcedures } from "./api.js";

function selectedCallType(procedures) {
  const requested = new URLSearchParams(window.location.search).get("task");
  return procedures.some((procedure) => procedure.call_type === requested) ? requested : procedures[0]?.call_type;
}

export default function ProceduresPage() {
  const [procedures, setProcedures] = useState([]);
  const [error, setError] = useState(null);
  const [callType, setCallType] = useState(null);

  useEffect(() => {
    fetchProcedures().then((data) => {
      setProcedures(data.procedures);
      setCallType(selectedCallType(data.procedures));
    }).catch((reason) => setError(reason.message));
  }, []);

  const procedure = useMemo(
    () => procedures.find((item) => item.call_type === callType), [procedures, callType],
  );

  function choose(next) {
    setCallType(next);
    const url = new URL(window.location.href);
    url.searchParams.set("task", next);
    window.history.replaceState({}, "", url);
  }

  if (error) return <><h1>Procedures</h1><p className="error" role="alert">Could not load procedures: {error}</p></>;
  if (!procedure) return <><h1>Procedures</h1><p className="muted">Loading procedures…</p></>;

  return <section className="procedures-page">
    <header className="procedures-heading"><p className="eyebrow">Preparation</p><h1>Procedures</h1><p>Review the required steps before your next call.</p></header>
    <div className="procedures-layout">
      <aside className="procedure-picker" aria-label="Task type">
        <p>Task type</p>
        {procedures.map((item) => <button key={item.call_type} type="button" aria-pressed={item.call_type === callType}
          className={item.call_type === callType ? "selected" : ""} onClick={() => choose(item.call_type)}>{item.name}</button>)}
      </aside>
      <div className="procedure-content">
        <section className="procedure-summary"><p className="eyebrow">{procedure.steps.length} required steps</p><h2>{procedure.name}</h2><p>{procedure.description}</p></section>
        <ol className="procedure-steps">
          {procedure.steps.map((step) => <li key={step.key}>
            <span className="procedure-stone" aria-hidden="true">{step.order}</span>
            <article><h3>{step.step_name}</h3><p>{step.step_description}</p></article>
          </li>)}
        </ol>
      </div>
    </div>
  </section>;
}
