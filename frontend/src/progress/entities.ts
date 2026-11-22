// What the app knows about an agent's progress. Types only: every number, order and sentence comes from the server.

export type StepResultStatus = "completed" | "missed" | "wrong";

export type ProgressWeek = {
  weekStart: string; // the Monday, YYYY-MM-DD
  stepsCompleted: number;
  stepsTotal: number;
  percent: number | null;
  isCurrent: boolean;
};

export type WeekNumbers = { stepsCompleted: number; stepsTotal: number; percent: number | null };

export type CallTypeProgress = {
  callType: string;
  name: string;
  stepsCompleted: number;
  stepsTotal: number;
  percent: number | null;
  calls: number;
};

export type StepRow = {
  stepKey: string;
  name: string;
  callType: string | null; // null: a step every call type has
  label: string;
  results: string[]; // oldest first; normally a StepResultStatus
  misses: number;
  window: number;
  summary: string;
};

export type Progress = {
  demoData: boolean;
  weeks: ProgressWeek[];
  thisWeek: WeekNumbers | null;
  firstWeekPercent: number | null;
  comparison: string | null;
  callTypes: CallTypeProgress[];
  steps: StepRow[];
};
