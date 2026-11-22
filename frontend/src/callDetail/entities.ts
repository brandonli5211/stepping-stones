// What the app knows about one stored call. Types only: the score, counts, notes and flags all come from the server.

export type Severity = "none" | "slip" | "inaccuracy" | "mistake" | "critical";

export type Score = {
  score: number | null; // null: the call has no step results yet
  outOf: number;
  stepsDoneRight: number;
  stepsTotal: number;
  pointsLost: number;
  criticalCount: number;
  pointsUnderReview: number;
  provisional: boolean; // true while points are under review
};

export type Note = {
  kind: "evidence" | "wrong";
  stepKey: string;
  text: string; // "Evidence for Greet and open" / "Wrong: ..."
};

export type Turn = {
  idx: number; // from 1, in call order
  speaker: "agent" | "caller";
  startSeconds: number | null;
  text: string;
  notes: Note[];
};

export type Flag = {
  stepKey: string;
  stepName: string;
  status: "missed" | "wrong";
  severity: Severity;
  pointsLost: number;
  message: string | null;
};

export type CallDetail = {
  callId: number;
  externalId: string;
  callTypeName: string;
  summary: string | null;
  score: Score;
  turns: Turn[];
  flags: Flag[];
};
