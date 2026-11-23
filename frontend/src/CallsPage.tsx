import { useEffect, useState } from "react";
import { PageHeader, ScoreRing, StateMessage, StatusLegend, Stone } from "./components/pieces";
import { Card, CardContent } from "./components/ui/card";
import { fetchCalls } from "./api.js";

const CALL_TYPES = [
  ["transfer_money", "Transfer money"], ["check_balance", "Check balance"],
  ["replace_card", "Replace card"], ["schedule_appointment", "Schedule appointment"],
  ["order_checks", "Order checks"], ["reset_password", "Reset password"],
  ["pay_bill", "Pay bill"], ["get_branch_hours", "Get branch hours"],
] as const;

type CallStep = { key: string; name: string; status: string };
type Call = {
  id: number; external_id: string; call_type_name: string; started_at: string; status: string;
  score: number | null; steps_completed: number; steps_total: number; steps: CallStep[];
  result: { label: string } | null;
};
type CallsResponse = {
  summary: { calls_reviewed: number; weeks: number | null; this_week: { percent: number | null; steps_completed: number; steps_total: number } | null; first_week_percent: number | null };
  calls: Call[];
};

function formatDate(iso: string) {
  const date = new Date(iso);
  return {
    day: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    time: date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
  };
}

function resultText(call: Call) {
  if (call.status === "pending") return "Not analysed yet";
  if (call.result) return call.result.label;
  if (call.status === "needs_review" || call.steps.some((step) => step.status === "under_review")) return "Needs review";
  return "All steps completed";
}

function readFilters() {
  const search = new URLSearchParams(window.location.search);
  return { callType: search.get("call_type") ?? "", hasMissed: search.get("has_missed") === "true" };
}

function syncFilters(callType: string, hasMissed: boolean) {
  const search = new URLSearchParams(window.location.search);
  callType ? search.set("call_type", callType) : search.delete("call_type");
  hasMissed ? search.set("has_missed", "true") : search.delete("has_missed");
  const query = search.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`);
}

function ThisWeek({ summary }: { summary: CallsResponse["summary"] }) {
  const week = summary.this_week;
  const comparison = week && summary.first_week_percent != null && week.percent != null
    ? week.percent > summary.first_week_percent ? `Up from ${summary.first_week_percent}% in week 1`
      : week.percent < summary.first_week_percent ? `Down from ${summary.first_week_percent}% in week 1`
        : `Same as ${summary.first_week_percent}% in week 1`
    : null;
  return (
    <Card>
      <CardContent className="flex flex-col gap-5 pt-6 sm:flex-row sm:items-center">
        <ScoreRing value={week?.percent ?? null} size={92} />
        <div className="min-w-0 flex-1">
          <p className="text-sm text-muted">This week</p>
          <p className="mt-1 text-lg font-semibold">{week ? `${week.steps_completed} of ${week.steps_total} required steps completed` : "No analysed calls this week"}</p>
          {comparison && <p className="mt-1 text-sm text-muted">{comparison}</p>}
        </div>
        <a className="shrink-0 rounded-lg bg-brand-soft px-4 py-2 text-center text-sm font-medium text-brand hover:bg-brand/20" href="/progress">See your progress</a>
      </CardContent>
    </Card>
  );
}

export default function CallsPage() {
  const initial = readFilters();
  const [callType, setCallType] = useState(initial.callType);
  const [hasMissed, setHasMissed] = useState(initial.hasMissed);
  const [data, setData] = useState<CallsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    syncFilters(callType, hasMissed);
    setError(null);
    void fetchCalls({ callType, hasMissed }).then((response: CallsResponse) => {
      if (active) setData(response);
    }).catch((reason: Error) => {
      if (active) setError(reason.message);
    });
    return () => { active = false; };
  }, [callType, hasMissed]);

  const subtitle = data ? `${data.summary.calls_reviewed} calls reviewed${data.summary.weeks ? ` in the last ${data.summary.weeks} weeks` : ""}.` : "Review recent calls and the steps behind each score.";
  return (
    <>
      <PageHeader title="Your calls" subtitle={subtitle} />
      {error && <Card><CardContent><StateMessage kind="error" title="Couldn't load your calls" message={error} /></CardContent></Card>}
      {!data && !error && <p className="text-muted" role="status">Loading your calls…</p>}
      {data && <div className="flex flex-col gap-6">
        <ThisWeek summary={data.summary} />
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 rounded-lg border border-review/40 bg-white px-3 py-2 text-sm font-medium">
              Call type
              <select className="bg-transparent text-ink outline-none" aria-label="Call type" value={callType} onChange={(event) => setCallType(event.target.value)}>
                <option value="">All types</option>
                {CALL_TYPES.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
              </select>
            </label>
            <button type="button" aria-pressed={hasMissed} onClick={() => setHasMissed(!hasMissed)} className={`rounded-lg border px-4 py-2 text-sm font-medium ${hasMissed ? "border-brand bg-brand text-white" : "border-review/40 bg-white text-ink hover:bg-brand-soft"}`}>
              Has missed steps
            </button>
          </div>
          <StatusLegend />
        </div>
        <Card>
          <CardContent className="overflow-x-auto pt-2">
            {data.calls.length === 0 ? <StateMessage kind="empty" title="No calls match these filters" /> : (
              <table className="w-full min-w-[42rem] text-left text-sm">
                <thead className="border-b border-black/10 text-xs font-medium uppercase tracking-wide text-muted">
                  <tr><th className="px-2 py-3">Date</th><th className="px-2 py-3">Call type</th><th className="px-2 py-3">Steps</th><th className="px-2 py-3">Score</th><th className="px-2 py-3">Result</th></tr>
                </thead>
                <tbody className="divide-y divide-black/5">
                  {data.calls.map((call) => {
                    const when = formatDate(call.started_at);
                    const result = resultText(call);
                    const flagged = call.result != null || call.status === "needs_review";
                    return <tr key={call.id} className="align-middle">
                      <td className="px-2 py-4"><p className="font-medium">{when.day}</p><p className="text-xs text-muted">{when.time}</p></td>
                      <td className="px-2 py-4"><a href={`/calls/${call.id}`} className="font-semibold text-ink hover:text-brand hover:underline">{call.call_type_name}</a><p className="text-xs text-muted">Call {call.external_id}</p></td>
                      <td className="px-2 py-4"><div className="flex flex-wrap gap-1" aria-label="Step results">{call.steps.map((step) => <Stone key={step.key} status={step.status} label={step.name} size={21} />)}</div></td>
                      <td className="px-2 py-4">{call.score == null ? <span className="text-muted">–</span> : <><p className="font-semibold">{call.score}%</p><p className="text-xs text-muted">{call.steps_completed} of {call.steps_total}</p></>}</td>
                      <td className={`px-2 py-4 ${flagged ? "font-medium text-bad" : "text-muted"}`}>{result}</td>
                    </tr>;
                  })}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>}
    </>
  );
}
