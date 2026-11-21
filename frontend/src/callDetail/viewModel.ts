import type { ScoreBand } from "../domain";
import type { Severity } from "./entities";

// View Model for the call detail page: exactly what the page draws. The presenter sets it, the page subscribes.

export type TurnTone = "plain" | "evidence" | "wrong";

export type TurnLabelView = { kind: "evidence" | "wrong"; text: string };

export type TurnView = {
  idx: number;
  speakerLabel: string; // "Agent" or "Customer"
  timeText: string | null; // "0:33"
  text: string;
  tone: TurnTone;
  labels: TurnLabelView[];
  stepKeys: string[]; // the steps this turn has a note for
};

export type FlagCardView = { stepKey: string; title: string; pointsText: string; message: string | null; severity: Severity };

export type CallDetailReadyState = {
  kind: "ready";
  header: { title: string; reference: string; backHref: string; backLabel: string };
  score: {
    value: number | null;
    band: ScoreBand | null;
    bandLabel: string; // "Focus here" or "Not scored yet"
    stepsText: string; // "6 of 7"
    lostText: string | null; // "1 critical, 55 points lost"
    reviewText: string | null; // "10 points under review"
    provisional: boolean;
    summary: string | null;
  };
  transcript: { countText: string; empty: boolean; turns: TurnView[] };
  flags: { countText: string | null; empty: boolean; cards: FlagCardView[] };
};

export type CallDetailViewState =
  | { kind: "loading"; message: string }
  | { kind: "error"; title: string; message: string }
  | { kind: "notFound"; title: string; backHref: string }
  | CallDetailReadyState;

export const LOADING_MESSAGE = "Loading this call…";

export class CallDetailViewModel {
  private state: CallDetailViewState = { kind: "loading", message: LOADING_MESSAGE };
  private selected: string | null = null;
  private readonly listeners = new Set<() => void>();

  // arrow functions so React's useSyncExternalStore can take them as they are
  getState = (): CallDetailViewState => this.state;

  setState = (state: CallDetailViewState): void => {
    this.state = state;
    this.notify();
  };

  // the step the agent chose; kept apart from the state so a reload does not lose it (#36 shares it)
  selectedStepKey = (): string | null => this.selected;

  selectStep = (stepKey: string | null): void => {
    if (stepKey === this.selected) return;
    this.selected = stepKey;
    this.notify();
  };

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  };

  private notify(): void {
    this.listeners.forEach((listener) => listener());
  }
}
