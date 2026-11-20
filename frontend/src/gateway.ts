import type { ApiGateway } from "./application";

// fake answers for sample mode. same shape as GET /calls in backend/app/calls_api.py.
// scores, statuses and labels are typed in as-is, the server decides those, not us
const SAMPLE: Record<string, unknown> = {
  "/calls": {
    summary: {
      calls_reviewed: 48,
      weeks: 8,
      this_week: { steps_completed: 35, steps_total: 39, percent: 90 },
      first_week_percent: 64,
    },
    calls: [
      {
        id: 1, external_id: "HVB-DEMO-01", call_type: "replace_card", call_type_name: "Replace card",
        started_at: "2026-10-09T16:20:00Z", status: "analysed", score: 75, steps_completed: 3, steps_total: 4,
        steps: [
          { key: "greet", name: "Greet and open", status: "completed" },
          { key: "verify", name: "Verify identity", status: "completed" },
          { key: "confirm_ordered", name: "Confirm ordered", status: "missed" },
          { key: "close", name: "Close", status: "completed" },
        ],
        result: { label: "Missed Confirm ordered", status: "missed" },
      },
      {
        id: 2, external_id: "HVB-DEMO-02", call_type: "transfer_money", call_type_name: "Transfer money",
        started_at: "2026-10-09T14:05:00Z", status: "analysed", score: 80, steps_completed: 4, steps_total: 5,
        steps: [
          { key: "greet", name: "Greet and open", status: "completed" },
          { key: "amount", name: "Collect amount", status: "completed" },
          { key: "source", name: "Collect source account", status: "completed" },
          { key: "submit", name: "Submit and confirm", status: "wrong" },
          { key: "close", name: "Close", status: "under_review" },
        ],
        result: { label: "Wrong: Submit and confirm", status: "wrong" },
      },
    ],
  },
  // same shape as GET /progress. every number and sentence is typed in, the server writes those, not us
  "/progress": {
    demo_data: true,
    weeks: [
      { week_start: "2026-08-17", steps_completed: 16, steps_total: 25, percent: 64, is_current: false },
      { week_start: "2026-08-24", steps_completed: 16, steps_total: 23, percent: 70, is_current: false },
      { week_start: "2026-08-31", steps_completed: 17, steps_total: 25, percent: 68, is_current: false },
      { week_start: "2026-09-07", steps_completed: 24, steps_total: 32, percent: 75, is_current: false },
      { week_start: "2026-09-14", steps_completed: 45, steps_total: 56, percent: 80, is_current: false },
      { week_start: "2026-09-21", steps_completed: 31, steps_total: 39, percent: 79, is_current: false },
      { week_start: "2026-09-28", steps_completed: 19, steps_total: 22, percent: 86, is_current: false },
      { week_start: "2026-10-05", steps_completed: 35, steps_total: 39, percent: 90, is_current: true },
    ],
    this_week: { steps_completed: 35, steps_total: 39, percent: 90 },
    first_week_percent: 64,
    comparison: "Up from 64% in week 1",
    call_types: [
      { call_type: "replace_card", name: "Replace card", steps_completed: 3, steps_total: 4, percent: 75, calls: 1 },
      { call_type: "transfer_money", name: "Transfer money", steps_completed: 3, steps_total: 4, percent: 75, calls: 1 },
    ],
    steps: [
      {
        step_key: "confirm_ordered", name: "Confirm ordered", call_type: "replace_card", label: "Replace card",
        results: ["missed"], misses: 1, window: 1, summary: "Missed on your last replace-card call",
      },
      {
        step_key: "submit", name: "Submit and confirm", call_type: "transfer_money", label: "Transfer money",
        results: ["wrong"], misses: 1, window: 1, summary: "Missed on your last transfer-money call",
      },
      {
        step_key: "greet", name: "Greet and open", call_type: null, label: "All call types",
        results: ["completed", "completed"], misses: 0, window: 2, summary: "Done on all of your last 2 calls",
      },
    ],
  },
};

// sample mode answers from SAMPLE, otherwise it's a plain fetch to the api
export function createApiGateway(opts: { apiUrl: string; sampleData: boolean; fetchImpl?: typeof fetch }): ApiGateway {
  return {
    async get<T>(path: string): Promise<T> {
      if (opts.sampleData) {
        // the sample is the same whatever the query string asks for
        const key = path.split("?")[0];
        if (!(key in SAMPLE)) throw new Error(`no sample data for ${path}`);
        return structuredClone(SAMPLE[key]) as T;
      }
      const res = await (opts.fetchImpl ?? fetch)(`${opts.apiUrl}${path}`);
      if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
      return res.json() as Promise<T>;
    },
  };
}
