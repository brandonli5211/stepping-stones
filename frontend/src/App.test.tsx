import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";

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

test("call detail shows the call and keeps my calls marked", () => {
  window.history.pushState(null, "", "/calls/7");
  render(<App />);
  expect(screen.getByRole("heading", { name: "Call 7" })).toBeTruthy();
  expect(marked()).toBe("My calls");
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
