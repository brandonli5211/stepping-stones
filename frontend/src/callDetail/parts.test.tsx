import { fireEvent, render, screen } from "@testing-library/react";
import { FlagList, ScorePanel, StepList, StepPanel, Transcript } from "./parts";
import type { CallDetailReadyState } from "./viewModel";

const score: CallDetailReadyState["score"] = {
  value: 45, outOfText: "of 100", band: "focus_here", bandLabel: "Focus here", stepsText: "6 of 7 steps done right",
  lostText: "1 critical, 55 points lost", reviewText: null, provisional: false, summary: "The accounts were reversed.",
};

const transcript: CallDetailReadyState["transcript"] = {
  countText: "3 turns, verbatim", empty: false,
  turns: [
    { idx: 2, speakerLabel: "Agent", timeText: "0:02", text: "thank you for calling", tone: "evidence",
      labels: [{ kind: "evidence", text: "Evidence for Greet and open" }], stepKeys: ["greet_and_open"] },
    { idx: 9, speakerLabel: "Agent", timeText: "0:33", text: "from your savings", tone: "wrong",
      labels: [{ kind: "wrong", text: "Wrong: read back reversed" }], stepKeys: ["submit"] },
    { idx: 10, speakerLabel: "Customer", timeText: null, text: "yes", tone: "plain", labels: [], stepKeys: [] },
  ],
};

const flags: CallDetailReadyState["flags"] = {
  countText: "1 critical", empty: false,
  cards: [{ stepKey: "submit", title: "Submit and confirm transfer", pointsText: "−55 points", message: "Moved it the wrong way.", severity: "critical" }],
};

test("ScorePanel shows the score, band, steps, points lost and summary", () => {
  render(<ScorePanel score={score} />);
  expect(screen.getByRole("img", { name: "Score 45%" }).textContent).toContain("45");
  expect(screen.getByText("of 100 · Focus here")).toBeTruthy();
  expect(screen.getByText("6 of 7 steps done right")).toBeTruthy();
  expect(screen.getByText("1 critical, 55 points lost")).toBeTruthy();
  expect(screen.getByText("The accounts were reversed.")).toBeTruthy();
});

test("ScorePanel without a score says so", () => {
  render(<ScorePanel score={{ ...score, value: null, band: null, bandLabel: "Not scored yet", lostText: null, summary: null }} />);
  expect(screen.getByText("Not scored yet")).toBeTruthy();
  expect(screen.queryByText(/points lost/)).toBeNull();
});

test("Transcript draws each turn with its labels, each label with its stone", () => {
  render(<Transcript transcript={transcript} selectedStepKey={null} />);
  const turns = screen.getAllByRole("listitem");
  expect(turns).toHaveLength(3);
  expect(turns.map((t) => t.dataset.tone)).toEqual(["evidence", "wrong", "plain"]);
  expect(turns[1].textContent).toContain("0:33");
  expect(screen.getByText("Wrong: read back reversed")).toBeTruthy();
  expect(turns[1].querySelector("[data-status='wrong']")).not.toBeNull();
  expect(turns[0].querySelector("[data-status='completed']")).not.toBeNull();
  expect(turns.every((t) => t.dataset.selected === "false")).toBe(true);
});

test("Transcript highlights the chosen step's turns and scrolls the first into view", () => {
  const scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = scrollIntoView;
  render(<Transcript transcript={transcript} selectedStepKey="submit" />);
  const turns = screen.getAllByRole("listitem");
  expect(turns.map((t) => t.dataset.selected)).toEqual(["false", "true", "false"]);
  expect(scrollIntoView).toHaveBeenCalledTimes(1);
  expect(scrollIntoView.mock.instances[0]).toBe(turns[1]);
});

test("Transcript with nothing to show", () => {
  render(<Transcript transcript={{ countText: "0 turns, verbatim", empty: true, turns: [] }} selectedStepKey={null} />);
  expect(screen.getByText("Transcript not available")).toBeTruthy();
});

test("FlagList cards select their step", () => {
  const onSelect = vi.fn();
  render(<FlagList flags={flags} selectedStepKey={null} onSelect={onSelect} />);
  const card = screen.getByRole("button", { name: /Submit and confirm transfer/ });
  expect(card.textContent).toContain("−55 points");
  expect(card.textContent).toContain("Moved it the wrong way.");
  fireEvent.click(card);
  expect(onSelect).toHaveBeenCalledWith("submit");
});

test("StepList selects a step and says when there are none", () => {
  const onSelect = vi.fn();
  const { rerender } = render(<StepList rows={[]} selectedStepKey={null} onSelect={onSelect} />);
  expect(screen.getByText("No required steps on this call")).toBeTruthy();
  rerender(<StepList rows={[{ key: "greet_and_open", name: "Greet and open", statusLabel: "Completed", pointsText: "", failed: false }]} selectedStepKey={null} onSelect={onSelect} />);
  fireEvent.click(screen.getByRole("button", { name: "Required step: Greet and open" }));
  expect(onSelect).toHaveBeenCalledWith("greet_and_open");
});

test("StepPanel draws the quote and says when there is no step or no quote", () => {
  const { rerender } = render(<StepPanel panel={null} />);
  expect(screen.getByText("Select a step to see what it asked for.")).toBeTruthy();
  rerender(<StepPanel panel={{
    key: "close", name: "Close", description: "Thank the caller.", reason: null, statusLabel: "Missed",
    worthText: "Worth 5 points", lostText: "−5 points", severityLabel: "Slip", subChecks: [],
    evidence: null, coaching: "Next time, thank them.", comparison: null,
  }} />);
  expect(screen.getByText("No quote stored for this step")).toBeTruthy();
  expect(screen.getByText("Next time, thank them.")).toBeTruthy();
});

test("FlagList with no flags", () => {
  render(<FlagList flags={{ countText: null, empty: true, cards: [] }} selectedStepKey={null} onSelect={vi.fn()} />);
  expect(screen.getByText("Nothing to fix on this call")).toBeTruthy();
});
