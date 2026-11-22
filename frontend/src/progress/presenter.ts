import type { CallTypeProgress, ProgressWeek, StepRow, WeekNumbers } from "./entities";
import type { ViewProgressOutputBoundary } from "./outputBoundary";
import type { ViewProgressOutputData } from "./outputData";
import {
  LOADING_MESSAGE,
  type CallTypeBarView,
  type ProgressViewModel,
  type StepRowView,
  type WeekBarView,
} from "./viewModel";

export const FIRST_STEP_ROWS = 5;

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Presenter for ViewProgress: shapes the server's answer for the page. Formatting only.
// Percents, counts, order, the comparison line and the summary lines are the server's and are not changed here.
export class ViewProgressPresenter implements ViewProgressOutputBoundary {
  constructor(private readonly viewModel: ProgressViewModel) {}

  prepareLoadingView(): void {
    this.viewModel.setState({ kind: "loading", message: LOADING_MESSAGE });
  }

  prepareFailView(message: string): void {
    this.viewModel.setState({ kind: "error", title: "Couldn't load your progress", message });
  }

  prepareSuccessView(output: ViewProgressOutputData): void {
    const progress = output.progress;
    if (progress.callTypes.length === 0 && progress.steps.length === 0) {
      this.viewModel.setState({
        kind: "empty", showDemoBadge: progress.demoData, message: "No analysed calls in the last 8 weeks",
      });
      return;
    }
    const allSteps = progress.steps.map((row) => this.stepRow(row));
    this.viewModel.setState({
      kind: "ready",
      showDemoBadge: progress.demoData,
      weeks: progress.weeks.map((week) => this.weekBar(week)),
      thisWeekText: this.thisWeekText(progress.thisWeek),
      comparison: progress.comparison,
      callTypes: progress.callTypes.map((type) => this.callTypeBar(type)),
      firstSteps: allSteps.slice(0, FIRST_STEP_ROWS),
      allSteps,
      showAllLabel: allSteps.length > FIRST_STEP_ROWS ? `Show all ${allSteps.length} steps` : null,
      showFewerLabel: "Show fewer",
    });
  }

  // "2026-08-17" -> "Aug 17". Split by hand so the viewer's time zone cannot move the day.
  weekLabel(weekStart: string): string {
    const [, month, day] = weekStart.split("-").map(Number);
    return `${MONTHS[month - 1]} ${day}`;
  }

  percentText(percent: number | null): string {
    return percent == null ? "–" : `${percent}%`;
  }

  // a percent as a bar length: 0–100
  barSize(percent: number | null): number {
    return percent == null ? 0 : Math.min(100, Math.max(0, percent));
  }

  thisWeekText(week: WeekNumbers | null): string {
    if (week == null || week.stepsTotal === 0) return "No analysed calls this week";
    return `${week.stepsCompleted} of ${week.stepsTotal} required steps completed`;
  }

  weekBar(week: ProgressWeek): WeekBarView {
    return {
      label: this.weekLabel(week.weekStart),
      percentText: this.percentText(week.percent),
      height: this.barSize(week.percent),
      isCurrent: week.isCurrent,
      currentText: week.isCurrent ? "This week" : null,
    };
  }

  callTypeBar(type: CallTypeProgress): CallTypeBarView {
    return {
      key: type.callType,
      name: type.name,
      percentText: this.percentText(type.percent),
      stepsText: `${type.stepsCompleted} of ${type.stepsTotal} steps`,
      width: this.barSize(type.percent),
    };
  }

  stepRow(row: StepRow): StepRowView {
    return {
      key: `${row.callType ?? "all"}:${row.stepKey}`,
      name: row.name,
      label: row.label,
      stones: row.results.map((status) => ({ status })),
      summary: row.summary,
    };
  }
}
