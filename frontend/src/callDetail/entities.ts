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

export type StepStatus = "completed" | "missed" | "wrong" | "under_review";

export type SubCheckResult = "passed" | "failed" | "under_review";

export type FieldResult = "match" | "mismatch" | "reversed";

export type SubCheck = {
  key: string;
  description: string;
  points: number;
  result: SubCheckResult;
};

export type StepEvidence = {
  quote: string;
  turnIdx: number;
  startSeconds: number | null;
};

// one required step, as the server stored it. the page does not decide the result.
export type Step = {
  key: string;
  position: number;
  name: string;
  status: StepStatus;
  severity: Severity;
  points: number;
  pointsLost: number;
  pointsUnderReview: number;
  description: string | null;
  detail: string | null;
  subChecks: SubCheck[];
  evidence: StepEvidence | null;
  coaching: string | null;
};

export type FieldRow = {
  field: string;
  label: string;
  callerAsked: string | null;
  logged: string | null;
  result: FieldResult;
};

export type TypeDetails = {
  type: string;
  fields: FieldRow[];
};

export type CallDetail = {
  callId: number;
  externalId: string;
  callType: string;
  callTypeName: string;
  summary: string | null;
  score: Score;
  turns: Turn[];
  steps: Step[];
  flags: Flag[];
  typeDetails: TypeDetails;
};
