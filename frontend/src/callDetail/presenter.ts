import { BAND_LABELS, scoreBand } from "../domain";
import type { Flag, Note, Score, Severity, Turn } from "./entities";
import type { ViewCallDetailOutputBoundary } from "./outputBoundary";
import type { ViewCallDetailOutputData } from "./outputData";
import {
  LOADING_MESSAGE,
  type CallDetailReadyState,
  type CallDetailViewModel,
  type FlagCardView,
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
    });
  }

  scoreView(score: Score, summary: string | null): CallDetailReadyState["score"] {
    const band = scoreBand(score.score);
    return {
      value: score.score,
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
