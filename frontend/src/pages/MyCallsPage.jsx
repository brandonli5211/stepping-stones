import { useState } from "react";
import { useApi } from "../api.js";
import { Card } from "../components/Card.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { SummaryCard } from "../components/ScoreRing.jsx";
import { StatusLegend, StoneRow } from "../components/Stone.jsx";
import { Link, paths } from "../router.jsx";

const hasProblem = (call) => call.steps.some((s) => s.status === "missed" || s.status === "wrong");

/** "Missed Confirm ordered" or "All steps completed". */
function resultText(call) {
  const step = call.steps.find((s) => s.status === "missed" || s.status === "wrong");
  return step ? `${step.status === "wrong" ? "Wrong" : "Missed"} ${step.name}` : "All steps completed";
}

export default function MyCallsPage() {
  const data = useApi("/api/calls");
  const [callType, setCallType] = useState("");
  const [onlyMissed, setOnlyMissed] = useState(false);
  if (!data) return null;

  const { summary, calls } = data;
  const callTypes = [...new Set(calls.map((c) => c.callType))];
  const visible = calls.filter((c) => (!callType || c.callType === callType) && (!onlyMissed || hasProblem(c)));

  return (
    <>
      <PageHeader
        title="Your calls"
        subtitle={`${summary.callsReviewed} calls reviewed in the last ${summary.weeks} weeks. Showing the ${calls.length} most recent.`}
      />
      <div className="stack">
        <SummaryCard
          summary={summary}
          action={
            <Link to={paths.progress} className="button summary__action">
              See your progress
            </Link>
          }
        />

        <div className="row toolbar">
          <label className="button button--outline">
            <span className="muted">Call type</span>
            <select value={callType} onChange={(e) => setCallType(e.target.value)}>
              <option value="">All types</option>
              {callTypes.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <button
            className={`button button--outline ${onlyMissed ? "is-active" : ""}`}
            aria-pressed={onlyMissed}
            onClick={() => setOnlyMissed(!onlyMissed)}
          >
            Has missed steps
          </button>
          <StatusLegend />
        </div>

        <Card className="table-card">
          <table className="table">
            <thead>
              <tr>
                {["Date", "Call type", "Steps", "Score", "Result"].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((call) => (
                <tr key={call.id}>
                  <td>
                    <b>{call.date}</b>
                    <small>{call.time}</small>
                  </td>
                  <td>
                    <Link to={paths.callDetail(call.id)}>
                      <b>{call.callType}</b>
                    </Link>
                    <small>Call {call.id}</small>
                  </td>
                  <td>
                    <StoneRow steps={call.steps} />
                  </td>
                  <td>
                    <b>{call.score}%</b>
                    <small>
                      {call.completed} of {call.total}
                    </small>
                  </td>
                  <td className={hasProblem(call) ? "danger" : "muted"}>{resultText(call)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
