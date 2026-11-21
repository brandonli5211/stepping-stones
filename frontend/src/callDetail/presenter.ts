import type { Flag, Note, Score, Severity, Turn } from "./entities";
import type { TurnTone } from "./viewModel";

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
