// View Model for the Progress page: exactly what the page draws. The presenter sets it, the page subscribes.

export type WeekBarView = {
  label: string; // "Aug 17"
  percentText: string; // "64%" or "–"
  height: number; // 0–100, a CSS percentage
  isCurrent: boolean;
  currentText: string | null; // "This week" on the current week
};

export type CallTypeBarView = { key: string; name: string; percentText: string; stepsText: string; width: number };

export type StepRowView = { key: string; name: string; label: string; stones: { status: string }[]; summary: string };

export type ProgressReadyState = {
  kind: "ready";
  showDemoBadge: boolean;
  weeks: WeekBarView[];
  thisWeekText: string;
  comparison: string | null; // the server's line, unchanged
  callTypes: CallTypeBarView[];
  firstSteps: StepRowView[];
  allSteps: StepRowView[];
  showAllLabel: string | null; // null: nothing more to show
  showFewerLabel: string;
};

export type ProgressViewState =
  | { kind: "loading"; message: string }
  | { kind: "error"; title: string; message: string }
  | { kind: "empty"; showDemoBadge: boolean; message: string }
  | ProgressReadyState;

export const LOADING_MESSAGE = "Loading your progress…";

export class ProgressViewModel {
  private state: ProgressViewState = { kind: "loading", message: LOADING_MESSAGE };
  private readonly listeners = new Set<() => void>();

  // arrow functions so React's useSyncExternalStore can take them as they are
  getState = (): ProgressViewState => this.state;

  setState = (state: ProgressViewState): void => {
    this.state = state;
    this.listeners.forEach((listener) => listener());
  };

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  };
}
