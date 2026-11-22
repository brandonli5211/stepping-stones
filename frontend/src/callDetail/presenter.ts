import { BAND_LABELS, scoreBand } from "../domain";
import type { FieldResult, Flag, Note, Score, Severity, Step, StepStatus, SubCheckResult, Turn, TypeDetails } from "./entities";
import type { ViewCallDetailOutputBoundary } from "./outputBoundary";
import type { ViewCallDetailOutputData } from "./outputData";
import {
  LOADING_MESSAGE,
  type CallDetailReadyState,
  type CallDetailViewModel,
  type FlagCardView,
  type StepPanelView,
  type StepRowView,
  type TurnTone,
  type TurnView,
} from "./viewModel";

// Formatting helpers for the call detail presenter. They only word and arrange what the server sent.

// seconds from the start of the call as m:ss; 33.53 -> "0:33"
export function formatTime(seconds: number | null): string | null {
  if (seconds == null) return null;
  const whole = Math.max(0, Math.floor(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

const FILLER = new Set(["okay", "ok", "and", "um", "uh", "yeah", "mm hmm", "mhm"]);

// a turn with nothing to read: only [noise] / <unk> markers or a lone "okay". A turn with a note is never filler.
export function isFillerTurn(turn: Turn): boolean {
  if (turn.notes.length > 0) return false;
  const words = turn.text.replace(/\[[^\]]*\]|<[^>]*>/g, " ").trim().replace(/\s+/g, " ").toLowerCase();
  return words === "" || FILLER.has(words);
}

export function turnTone(notes: Note[]): TurnTone {
  if (notes.some((note) => note.kind === "wrong")) return "wrong";
  if (notes.some((note) => note.kind === "evidence")) return "evidence";
  return "plain";
}

// "1 critical, 55 points lost"; null when nothing was lost
export function lostText(score: Score): string | null {
  if (score.pointsLost <= 0) return null;
  const points = `${score.pointsLost} ${score.pointsLost === 1 ? "point" : "points"} lost`;
  return score.criticalCount > 0 ? `${score.criticalCount} critical, ${points}` : points;
}

const SEVERITY_ORDER: Severity[] = ["critical", "mistake", "inaccuracy", "slip", "none"];

const STATUS_LABELS: Record<StepStatus, string> = {
  completed: "Completed", missed: "Missed", wrong: "Wrong", under_review: "Under review",
};

const SEVERITY_LABELS: Record<Severity, string | null> = {
  none: null, slip: "Slip", inaccuracy: "Inaccuracy", mistake: "Mistake", critical: "Critical",
};

const SUB_LABELS: Record<SubCheckResult, string> = { passed: "Passed", failed: "Failed", under_review: "Under review" };

const FIELD_LABELS: Record<FieldResult, string> = { match: "Match", mismatch: "Doesn't match", reversed: "Reversed" };

const PROCEDURE_KEY = /^[a-z][a-z0-9_]*$/;

export function stepStatusLabel(status: StepStatus): string {
  return STATUS_LABELS[status];
}

// "−55 points"; empty when the step lost nothing
export function stepPointsText(pointsLost: number): string {
  if (pointsLost <= 0) return "";
  return `\u2212${pointsLost} ${pointsLost === 1 ? "point" : "points"}`;
}

// the first missed or wrong step, else the first step, else nothing
export function defaultStepKey(steps: Step[]): string | null {
  const ordered = [...steps].sort((a, b) => a.position - b.position);
  const failed = ordered.find((step) => step.status === "missed" || step.status === "wrong");
  return (failed ?? ordered[0])?.key ?? null;
}

export function procedureHref(callType: string): string {
  return PROCEDURE_KEY.test(callType) ? `/procedures?task=${callType}` : "/procedures";
}

function settledLoss(status: StepStatus): boolean {
  return status === "missed" || status === "wrong";
}

export function stepRow(step: Step): StepRowView {
  return {
    key: step.key,
    name: step.name,
    status: step.status,
    statusLabel: stepStatusLabel(step.status),
    // a pending step has not lost points yet, so the row keeps the "Under review" words
    pointsText: settledLoss(step.status) ? stepPointsText(step.pointsLost) : "",
  };
}

function shown(value: string | null): string {
  const text = value?.trim() ?? "";
  return text === "" ? "\u2014" : text;
}

// the selected step, worded. the field table is the server's result, and only on a missed or wrong transfer step.
export function stepPanel(step: Step, details: TypeDetails): StepPanelView {
  const failed = settledLoss(step.status);
  const comparison = failed && details.type === "transfer_money" && details.fields.length > 0
    ? details.fields.map((row) => ({
      label: row.label,
      callerAsked: shown(row.callerAsked),
      logged: shown(row.logged),
      resultLabel: FIELD_LABELS[row.result],
    }))
    : null;
  return {
    key: step.key,
    name: step.name,
    description: step.description,
    reason: step.detail,
    statusLabel: stepStatusLabel(step.status),
    worthText: `Worth ${step.points} ${step.points === 1 ? "point" : "points"}`,
    lostText: failed ? stepPointsText(step.pointsLost) || null : null,
    reviewText: step.pointsUnderReview > 0 ? `${step.pointsUnderReview} ${step.pointsUnderReview === 1 ? "point" : "points"} under review` : null,
    severityLabel: SEVERITY_LABELS[step.severity],
    subChecks: step.subChecks.map((check) => ({
      description: check.description,
      resultLabel: SUB_LABELS[check.result],
      // only a failed sub-check has lost its points; a pending one keeps its "Under review" label
      pointsText: check.result === "failed" ? stepPointsText(check.points) : "",
    })),
    evidence: step.evidence && { quote: step.evidence.quote, timeText: formatTime(step.evidence.startSeconds) },
    coaching: failed ? step.coaching : null,
    comparison,
  };
}

// "1 critical, 2 slip": flags counted per severity, most severe first; null when there are none
export function flagCountText(flags: Flag[]): string | null {
  const parts = SEVERITY_ORDER.flatMap((severity) => {
    const count = flags.filter((flag) => flag.severity === severity).length;
    return count > 0 ? [`${count} ${severity}`] : [];
  });
  return parts.length > 0 ? parts.join(", ") : null;
}

// Presenter for ViewCallDetail: shapes the stored call for the page. Formatting only; the score, counts,
// notes and flags are the server's and are not changed here.
export class ViewCallDetailPresenter implements ViewCallDetailOutputBoundary {
  constructor(private readonly viewModel: CallDetailViewModel) {}

  prepareLoadingView(): void {
    this.viewModel.setState({ kind: "loading", message: LOADING_MESSAGE });
  }

  prepareNotFoundView(): void {
    this.viewModel.setState({ kind: "notFound", title: "Call not found", backHref: "/" });
  }

  prepareFailView(message: string): void {
    this.viewModel.setState({ kind: "error", title: "Couldn't load this call", message });
  }

  prepareSuccessView(output: ViewCallDetailOutputData): void {
    const detail = output.detail;
    const turns = [...detail.turns].sort((a, b) => a.idx - b.idx).filter((t) => !isFillerTurn(t)).map((t) => this.turnView(t));
    const steps = [...detail.steps].sort((a, b) => a.position - b.position);
    this.viewModel.setState({
      kind: "ready",
      header: { title: detail.callTypeName, reference: detail.externalId, backHref: "/", backLabel: "Back to my calls" },
      score: this.scoreView(detail.score, detail.summary),
      transcript: { countText: `${turns.length} ${turns.length === 1 ? "turn" : "turns"}, verbatim`, empty: turns.length === 0, turns },
      flags: {
        countText: flagCountText(detail.flags),
        empty: detail.flags.length === 0,
        cards: detail.flags.map((f) => this.flagCard(f)),
      },
      steps: {
        rows: steps.map(stepRow),
        panels: Object.fromEntries(steps.map((step) => [step.key, stepPanel(step, detail.typeDetails)])),
        procedureHref: procedureHref(detail.callType),
        empty: steps.length === 0,
      },
    });
    const selected = this.viewModel.selectedStepKey();
    if (selected == null || !steps.some((step) => step.key === selected)) {
      this.viewModel.selectStep(defaultStepKey(steps));
    }
  }

  scoreView(score: Score, summary: string | null): CallDetailReadyState["score"] {
    const band = scoreBand(score.score);
    return {
      value: score.score,
      outOfText: `of ${score.outOf}`,
      band,
      bandLabel: band ? BAND_LABELS[band] : "Not scored yet",
      stepsText: `${score.stepsDoneRight} of ${score.stepsTotal} steps done right${score.provisional ? " so far" : ""}`,
      lostText: lostText(score),
      reviewText: score.pointsUnderReview > 0 ? `${score.pointsUnderReview} points under review` : null,
      provisional: score.provisional,
      summary,
    };
  }

  turnView(turn: Turn): TurnView {
    return {
      idx: turn.idx,
      speakerLabel: turn.speaker === "agent" ? "Agent" : "Customer",
      timeText: formatTime(turn.startSeconds),
      text: turn.text,
      tone: turnTone(turn.notes),
      labels: turn.notes.map((n) => ({ kind: n.kind, text: n.text })),
      stepKeys: [...new Set(turn.notes.map((n) => n.stepKey))],
    };
  }

  flagCard(flag: Flag): FlagCardView {
    return {
      stepKey: flag.stepKey,
      title: flag.stepName,
      pointsText: `\u2212${flag.pointsLost} ${flag.pointsLost === 1 ? "point" : "points"}`,
      message: flag.message,
      severity: flag.severity,
    };
  }
}
