import type { Flag, Note, Score, Turn } from "./entities";
import { flagCountText, formatTime, isFillerTurn, lostText, turnTone } from "./presenter";

const turn = (text: string, notes: Note[] = []): Turn => ({ idx: 1, speaker: "agent", startSeconds: 0, text, notes });
const evidence: Note = { kind: "evidence", stepKey: "greet_and_open", text: "Evidence for Greet and open" };
const wrong: Note = { kind: "wrong", stepKey: "submit_and_confirm_transfer", text: "Wrong: read back reversed" };
const score = (pointsLost: number, criticalCount: number): Score => ({
  score: 100 - pointsLost, outOf: 100, stepsDoneRight: 6, stepsTotal: 7, pointsLost, criticalCount,
  pointsUnderReview: 0, provisional: false,
});
const flag = (severity: Flag["severity"]): Flag => ({
  stepKey: "s", stepName: "S", status: "wrong", severity, pointsLost: 5, message: null,
});

test("formatTime gives m:ss", () => {
  expect(formatTime(33.53)).toBe("0:33");
  expect(formatTime(65)).toBe("1:05");
  expect(formatTime(0.54)).toBe("0:00");
  expect(formatTime(null)).toBeNull();
});

test("isFillerTurn: markers and lone filler words, never a turn with a note", () => {
  expect(isFillerTurn(turn("[noise]"))).toBe(true);
  expect(isFillerTurn(turn("<unk>"))).toBe(true);
  expect(isFillerTurn(turn("Okay"))).toBe(true);
  expect(isFillerTurn(turn("mm hmm [noise]"))).toBe(true);
  expect(isFillerTurn(turn("and"))).toBe(true);
  expect(isFillerTurn(turn("yes"))).toBe(false);
  expect(isFillerTurn(turn("okay and what is the amount"))).toBe(false);
  expect(isFillerTurn(turn("okay", [evidence]))).toBe(false);
});

test("turnTone: wrong beats evidence beats plain", () => {
  expect(turnTone([evidence, wrong])).toBe("wrong");
  expect(turnTone([evidence])).toBe("evidence");
  expect(turnTone([])).toBe("plain");
});

test("lostText words the points lost", () => {
  expect(lostText(score(55, 1))).toBe("1 critical, 55 points lost");
  expect(lostText(score(55, 0))).toBe("55 points lost");
  expect(lostText(score(1, 0))).toBe("1 point lost");
  expect(lostText(score(0, 0))).toBeNull();
});

test("flagCountText counts per severity, most severe first", () => {
  expect(flagCountText([flag("critical")])).toBe("1 critical");
  expect(flagCountText([flag("slip"), flag("critical"), flag("slip")])).toBe("1 critical, 2 slip");
  expect(flagCountText([])).toBeNull();
});
