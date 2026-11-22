import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";
import { SAMPLE_CALL_DETAIL } from "./sampleCallDetail";

// no real api in tests. calls page and progress both just get a failed fetch
beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  window.history.pushState(null, "", "/");
});

const marked = () => screen.getByRole("link", { current: "page" }).textContent;
// the calls page shows its own "could not load" alert once its fetch fails
const callsPageSettled = () => screen.findByText(/Could not load calls/);

test("menu click switches screen and marked item", async () => {
  render(<App />);
  await callsPageSettled();
  expect(marked()).toBe("My calls");
  fireEvent.click(screen.getByRole("link", { name: "Procedures" }));
  expect(screen.getByRole("heading", { name: "Procedures" })).toBeTruthy();
  expect(marked()).toBe("Procedures");
});

test("a direct procedure address restores its selected task", async () => {
  const procedures = {
    procedures: [{ call_type: "replace_card", name: "Replace card", description: "Replace it", steps: [] }],
  };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(procedures), { status: 200 })));
  window.history.pushState(null, "", "/procedures?task=replace_card");
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Replace card" })).toBeTruthy();
  expect(screen.getByRole("link", { current: "page" }).textContent).toBe("Procedures");
});

test("call detail shows the call and keeps my calls marked", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => SAMPLE_CALL_DETAIL }));
  window.history.pushState(null, "", "/calls/1");
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Transfer money" })).toBeTruthy();
  expect(String(vi.mocked(fetch).mock.calls[0][0])).toMatch(/\/calls\/1$/);
  expect(marked()).toBe("My calls");
});

test("a call in my calls opens its call detail page", async () => {
  const list = {
    summary: { calls_reviewed: 1, weeks: null, this_week: null, first_week_percent: null },
    calls: [{
      id: 1, external_id: "a2f086d27b3a4f96", call_type: "transfer_money", call_type_name: "Transfer money",
      started_at: "2026-10-07T20:48:00Z", status: "scored", score: 45, steps_completed: 6, steps_total: 7, steps: [], result: null,
    }],
  };
  const fetchMock = vi.fn(async (url: string) => ({
    ok: true, status: 200, json: async () => (new URL(url).pathname === "/calls/1" ? SAMPLE_CALL_DETAIL : list),
  }));
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);
  fireEvent.click(await screen.findByRole("link", { name: /Transfer money/ }));
  expect(window.location.pathname).toBe("/calls/1");
  expect(await screen.findByRole("heading", { name: "Transfer money" })).toBeTruthy();
  expect(fetchMock.mock.calls.some(([url]) => new URL(url).pathname === "/calls/1")).toBe(true);
});

test("call detail with an id that can't be a call shows not found without asking the api", async () => {
  window.history.pushState(null, "", "/calls/abc");
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Call not found" })).toBeTruthy();
  expect(fetch).not.toHaveBeenCalled();
});

test("call detail shows the error when the api is down", async () => {
  window.history.pushState(null, "", "/calls/7");
  render(<App />);
  expect((await screen.findByRole("alert")).textContent).toContain("Couldn't load this call");
});

test("unknown address shows my calls", async () => {
  window.history.pushState(null, "", "/nowhere");
  render(<App />);
  await callsPageSettled();
  expect(screen.getByRole("heading", { name: "Your calls" })).toBeTruthy();
});

test("progress shows the error message when the api is down", async () => {
  window.history.pushState(null, "", "/progress");
  render(<App />);
  expect((await screen.findByRole("alert")).textContent).toContain("Couldn't load your progress");
});

test("progress shows what the api sends", async () => {
  const body = {
    demo_data: true,
    weeks: [{ week_start: "2026-10-05", steps_completed: 53, steps_total: 59, percent: 90, is_current: true }],
    this_week: { steps_completed: 53, steps_total: 59, percent: 90 },
    first_week_percent: 64,
    comparison: "Up from 64% in week 1",
    call_types: [{ call_type: "check_balance", name: "Check balance", steps_completed: 42, steps_total: 48, percent: 88, calls: 8 }],
    steps: [
      {
        step_key: "confirm_replacement", name: "Confirm replacement", call_type: "replace_card", label: "Replace card",
        results: ["completed", "missed"], misses: 1, window: 2, summary: "Missed on 1 of your last 2 replace-card calls",
      },
      ...["a", "b", "c", "d", "e"].map((k) => ({
        step_key: k, name: `Step ${k}`, call_type: "pay_bill", label: "Pay bill",
        results: ["completed"], misses: 0, window: 1, summary: "Done on your last pay-bill call",
      })),
    ],
  };
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  window.history.pushState(null, "", "/progress");
  render(<App />);
  expect(await screen.findByText("Up from 64% in week 1")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/progress");
  expect(screen.getByText("Demo data")).toBeTruthy();
  expect(screen.getByText("53 of 59 required steps completed")).toBeTruthy();
  expect(screen.getByText("Missed on 1 of your last 2 replace-card calls")).toBeTruthy();
  expect(marked()).toBe("Progress");
  // 5 of the 6 rows first, then all of them
  expect(screen.queryByText("Step e")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Show all 6 steps" }));
  expect(screen.getByText("Step e")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Show fewer" }));
  expect(screen.queryByText("Step e")).toBeNull();
});

test("agent shows in the menu, 'Agent' when nothing is configured", async () => {
  render(<App />);
  await callsPageSettled();
  expect(screen.getByText("Agent")).toBeTruthy();
});
