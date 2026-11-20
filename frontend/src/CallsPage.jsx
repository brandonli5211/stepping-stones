import { useEffect, useState } from "react";
import { fetchCalls } from "./api.js";

const CALL_TYPES = [
  ["transfer_money", "Transfer money"],
  ["check_balance", "Check balance"],
  ["replace_card", "Replace card"],
  ["schedule_appointment", "Schedule appointment"],
  ["order_checks", "Order checks"],
  ["reset_password", "Reset password"],
  ["pay_bill", "Pay bill"],
  ["get_branch_hours", "Get branch hours"],
];

// Each step is a "stepping stone"; a few shapes so the row looks like stones, not a progress bar.
const STONE_SHAPES = ["50% 50% 50% 50% / 60% 60% 40% 40%", "50%", "50% 50% 50% 50% / 40% 40% 60% 60%", "60% 40% 55% 45% / 50% 50% 50% 50%"];

function Stone({ step, index }) {
  const kind = step.status === "completed" ? "done" : step.status === "under_review" ? "review" : "missed";
  const label = { done: "Completed", review: "Under review", missed: step.status === "wrong" ? "Wrong" : "Missed" }[kind];
  return <span className={`stone ${kind}`} style={{ borderRadius: STONE_SHAPES[index % 4] }} title={`${step.name}: ${label}`} />;
}

function formatDate(iso) {
  const d = new Date(iso);
  return {
    day: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    time: d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
  };
}

function resultOf(call) {
  if (call.status === "pending") return { text: "Not analysed yet", className: "muted" };
  if (call.result) return { text: call.result.label, className: "bad" };
  if (call.status === "needs_review") return { text: "Needs review", className: "muted" };
  if (call.steps.some((s) => s.status === "under_review")) return { text: "Some steps under review", className: "muted" };
  return { text: "All steps completed", className: "muted" };
}

function Ring({ percent }) {
  const r = 38;
  const c = 2 * Math.PI * r;
  return (
    <svg width="90" height="90" viewBox="0 0 90 90" aria-hidden="true">
      <circle cx="45" cy="45" r={r} fill="none" stroke="#d3e0e4" strokeWidth="8" />
      <circle cx="45" cy="45" r={r} fill="none" stroke="#3d6b7a" strokeWidth="8" strokeLinecap="round"
        strokeDasharray={`${(c * (percent ?? 0)) / 100} ${c}`} transform="rotate(-90 45 45)" />
      <text x="45" y="52" textAnchor="middle" fontSize="20" fontWeight="600" fill="#1d2b2f">{percent ?? "–"}%</text>
    </svg>
  );
}

function WeekCard({ summary }) {
  const week = summary.this_week;
  const first = summary.first_week_percent;
  let trend = null;
  if (week && first != null && week.percent != null) {
    trend = week.percent > first ? `Up from ${first}% in week 1` : week.percent < first ? `Down from ${first}% in week 1` : `Same as ${first}% in week 1`;
  }
  return (
    <section className="card week">
      <Ring percent={week?.percent} />
      <div className="week-text">
        <small>This week</small>
        <h2>{week && week.steps_total > 0 ? `${week.steps_completed} of ${week.steps_total} required steps completed` : "No analysed calls this week"}</h2>
        {trend && <p className="muted">{trend}</p>}
      </div>
      <button className="secondary" type="button">See your progress</button>
    </section>
  );
}

export default function CallsPage() {
  const [callType, setCallType] = useState("");
  const [hasMissed, setHasMissed] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let current = true;
    setError(null);
    fetchCalls({ callType, hasMissed })
      .then((d) => current && setData(d))
      .catch((e) => current && setError(e.message));
    return () => { current = false; };
  }, [callType, hasMissed]);

  return (
    <>
      <h1>Your calls</h1>
      {data && (
        <p className="muted">
          {data.summary.calls_reviewed} calls reviewed{data.summary.weeks ? ` in the last ${data.summary.weeks} weeks` : ""}.
          Showing the {data.calls.length} most recent.
        </p>
      )}
      {error && <p className="error" role="alert">Could not load calls: {error}</p>}
      {data && <WeekCard summary={data.summary} />}

      <div className="filters">
        <label className="select">Call type
          <select value={callType} onChange={(e) => setCallType(e.target.value)}>
            <option value="">All types</option>
            {CALL_TYPES.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
          </select>
        </label>
        <button type="button" className={`toggle${hasMissed ? " on" : ""}`} aria-pressed={hasMissed} onClick={() => setHasMissed(!hasMissed)}>
          Has missed steps
        </button>
        <span className="legend">
          <span><i className="stone done" /> Completed</span>
          <span><i className="stone missed" /> Missed</span>
          <span><i className="stone review" /> Under review</span>
        </span>
      </div>

      <section className="card">
        <table>
          <thead>
            <tr><th>Date</th><th>Call type</th><th>Steps</th><th>Score</th><th>Result</th></tr>
          </thead>
          <tbody>
            {data?.calls.map((call) => {
              const when = formatDate(call.started_at);
              const result = resultOf(call);
              return (
                <tr key={call.id}>
                  <td><strong>{when.day}</strong><small>{when.time}</small></td>
                  <td><strong>{call.call_type_name}</strong><small>Call {call.external_id}</small></td>
                  <td><span className="stones">{call.steps.map((s, i) => <Stone key={s.key} step={s} index={i} />)}</span></td>
                  <td>{call.score == null ? "–" : <><strong>{call.score}%</strong><small>{call.steps_completed} of {call.steps_total}</small></>}</td>
                  <td className={result.className}>{result.className === "bad" ? <strong>{result.text}</strong> : result.text}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {data && data.calls.length === 0 && <p className="empty muted">No calls match.</p>}
        {!data && !error && <p className="empty muted">Loading…</p>}
      </section>
    </>
  );
}
