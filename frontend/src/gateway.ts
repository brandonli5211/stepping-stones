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
};

// sample mode answers from SAMPLE, otherwise it's a plain fetch to the api
export function createApiGateway(opts: { apiUrl: string; sampleData: boolean; fetchImpl?: typeof fetch }): ApiGateway {
  return {
    async get<T>(path: string): Promise<T> {
      if (opts.sampleData) {
        if (!(path in SAMPLE)) throw new Error(`no sample data for ${path}`);
        return structuredClone(SAMPLE[path]) as T;
      }
      const res = await (opts.fetchImpl ?? fetch)(`${opts.apiUrl}${path}`);
      if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
      return res.json() as Promise<T>;
    },
  };
}
