import { fireEvent, render, screen } from "@testing-library/react";
import CallsPage from "./CallsPage";

const response = {
  summary: { calls_reviewed: 48, weeks: 8, this_week: { percent: 90, steps_completed: 35, steps_total: 39 }, first_week_percent: 64 },
  calls: [{
    id: 7, external_id: "HVB-DEMO-07", call_type_name: "Transfer money", started_at: "2026-11-18T18:04:00Z",
    status: "scored", score: 75, steps_completed: 3, steps_total: 4,
    steps: [{ key: "greet", name: "Greet", status: "completed" }, { key: "confirm", name: "Confirm", status: "missed" }],
    result: { label: "Missed Confirm transfer" },
  }],
};

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 })));
});

test("draws the Figma-aligned summary and the call table", async () => {
  render(<CallsPage />);
  expect(await screen.findByText("48 calls reviewed in the last 8 weeks.")).toBeTruthy();
  expect(screen.getByText("35 of 39 required steps completed")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Transfer money" }).getAttribute("href")).toBe("/calls/7");
  expect(screen.getByText("Missed Confirm transfer")).toBeTruthy();
});

test("restores and updates filters in the address", async () => {
  window.history.replaceState(null, "", "/?call_type=pay_bill&has_missed=true");
  render(<CallsPage />);
  await screen.findByText("48 calls reviewed in the last 8 weeks.");
  expect((screen.getByRole("combobox", { name: "Call type" }) as HTMLSelectElement).value).toBe("pay_bill");
  expect(screen.getByRole("button", { name: "Has missed steps" }).getAttribute("aria-pressed")).toBe("true");

  fireEvent.change(screen.getByRole("combobox", { name: "Call type" }), { target: { value: "" } });
  fireEvent.click(screen.getByRole("button", { name: "Has missed steps" }));
  expect(window.location.search).toBe("");
});
