import { Stone } from "../components/pieces";
import type { CallTypeBarView, StepRowView, WeekBarView } from "./viewModel";

// The drawn pieces of the Progress page. They only draw what the view model gives them.

export function WeekChart({ weeks }: { weeks: WeekBarView[] }) {
  return (
    <ol className="flex items-end gap-3" aria-label="Required steps completed, by week">
      {weeks.map((week) => (
        <li key={week.label} className="flex min-w-0 flex-1 flex-col items-center gap-1" data-current={week.isCurrent}>
          <span className={`text-sm ${week.isCurrent ? "font-bold text-ink" : "text-muted"}`}>{week.percentText}</span>
          <div className="flex h-40 w-full items-end rounded-lg bg-page">
            <div
              className={`w-full rounded-lg ${week.isCurrent ? "bg-brand" : "bg-brand-soft"}`}
              style={{ height: `${week.height}%` }}
              data-testid="week-bar"
            />
          </div>
          <span className="text-xs text-muted">{week.label}</span>
          <span className="h-4 text-xs font-semibold text-brand">{week.currentText}</span>
        </li>
      ))}
    </ol>
  );
}

export function CallTypeBars({ callTypes }: { callTypes: CallTypeBarView[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {callTypes.map((type) => (
        <li key={type.key} className="grid grid-cols-[11rem_1fr_3rem] items-center gap-4">
          <div className="min-w-0">
            <p className="text-sm font-medium break-words">{type.name}</p>
            <p className="text-xs text-muted">{type.stepsText}</p>
          </div>
          <div className="h-3 rounded-full bg-page">
            <div className="h-3 rounded-full bg-brand" style={{ width: `${type.width}%` }} data-testid="call-type-bar" />
          </div>
          <span className="text-right text-sm font-semibold">{type.percentText}</span>
        </li>
      ))}
    </ul>
  );
}

export function StepRows({ rows }: { rows: StepRowView[] }) {
  return (
    <ul className="flex flex-col divide-y divide-black/5">
      {rows.map((row) => (
        <li key={row.key} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-6 gap-y-1 py-3">
          <div className="min-w-0">
            <p className="text-sm font-medium break-words">{row.name}</p>
            <p className="text-xs text-muted">{row.label}</p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2" data-testid="step-stones">
            {row.stones.map((stone, i) => <Stone key={i} status={stone.status} size={24} />)}
          </div>
          <p className="col-span-2 text-xs text-muted">{row.summary}</p>
        </li>
      ))}
    </ul>
  );
}
