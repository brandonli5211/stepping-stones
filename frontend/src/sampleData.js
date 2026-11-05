// Example API responses used when VITE_SAMPLE_DATA=true.
// Keys are API paths (":param" allowed); values build the response.

const procedures = [
  ["replace-card", "Replace card", ["Greet and open", "Verify identity", "Confirm ordered", "Explain delivery"]],
  ["check-balance", "Check balance", ["Greet and open", "Verify identity", "Read balance"]],
  ["pay-bill", "Pay bill", ["Greet and open", "Collect payee", "Collect amount", "Confirm payment"]],
  [
    "transfer-money",
    "Transfer money",
    ["Greet and open", "Collect amount", "Collect source account", "Collect destination", "Submit and confirm"],
  ],
  ["reset-password", "Reset password", ["Greet and open", "Verify identity", "Send reset link", "Close"]],
  ["get-branch-hours", "Get branch hours", ["Greet and open", "Find branch", "Read hours"]],
].map(([id, callType, steps]) => ({ id, callType, steps }));

// [id, date, time, procedure, step codes]  c completed · m missed · w wrong · r under review
const STATUS = { c: "completed", m: "missed", w: "wrong", r: "review" };
const calls = [
  ["HVB-DEMO-01", "Oct 9", "16:20", "replace-card", "ccmc"],
  ["HVB-DEMO-02", "Oct 9", "14:05", "check-balance", "ccc"],
  ["HVB-DEMO-03", "Oct 9", "10:42", "pay-bill", "cccc"],
  ["HVB-DEMO-04", "Oct 8", "15:31", "replace-card", "ccmc"],
  ["HVB-DEMO-05", "Oct 8", "11:12", "replace-card", "cccc"],
  ["HVB-DEMO-06", "Oct 7", "16:48", "transfer-money", "cccwc"],
  ["HVB-DEMO-07", "Oct 7", "13:20", "reset-password", "cccr"],
  ["HVB-DEMO-08", "Oct 7", "09:58", "get-branch-hours", "ccc"],
  ["HVB-DEMO-09", "Oct 6", "14:12", "replace-card", "ccmc"],
  ["HVB-DEMO-10", "Oct 6", "09:40", "replace-card", "cccc"],
].map(([id, date, time, procedureId, codes]) => {
  const procedure = procedures.find((p) => p.id === procedureId);
  const steps = procedure.steps.map((name, i) => ({ name, status: STATUS[codes[i]] }));
  const completed = steps.filter((s) => s.status === "completed").length;
  const score = Math.round((completed / steps.length) * 100);
  return { id, date, time, callType: procedure.callType, steps, completed, total: steps.length, score };
});

const summary = { completed: 35, total: 39, score: 90, change: "Up from 64% in week 1", callsReviewed: 48, weeks: 8 };

export const sampleResponses = {
  "/api/me": () => ({ name: "Robert", role: "Agent" }),
  "/api/calls": () => ({ summary, calls }),
  "/api/calls/:callId": ({ callId }) => calls.find((c) => c.id === callId),
  "/api/progress": () => ({ summary }),
  "/api/procedures": () => procedures,
};
