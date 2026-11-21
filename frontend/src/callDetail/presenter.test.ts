import { SAMPLE_CALL_DETAIL } from "../sampleCallDetail";
import { CallDetailApi, type CallDetailDto } from "./api";
import type { CallDetail, Flag, Note, Score, Turn } from "./entities";
import { ViewCallDetailOutputData } from "./outputData";
import { flagCountText, formatTime, isFillerTurn, lostText, turnTone, ViewCallDetailPresenter } from "./presenter";
import { CallDetailViewModel, LOADING_MESSAGE, type CallDetailReadyState } from "./viewModel";

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

const sample = (): CallDetail =>
  new CallDetailApi({ get: async () => { throw new Error("unused"); } }).toCallDetail(SAMPLE_CALL_DETAIL as unknown as CallDetailDto);

function present(detail: CallDetail): CallDetailReadyState {
  const viewModel = new CallDetailViewModel();
  new ViewCallDetailPresenter(viewModel).prepareSuccessView(new ViewCallDetailOutputData(detail));
  const state = viewModel.getState();
  if (state.kind !== "ready") throw new Error(`expected ready, got ${state.kind}`);
  return state;
}

test("the sample call: header, score panel and flag", () => {
  const state = present(sample());
  expect(state.header).toEqual({ title: "Transfer money", reference: "a2f086d27b3a4f96", backHref: "/", backLabel: "Back to my calls" });
  expect(state.score).toMatchObject({
    value: 45, band: "focus_here", bandLabel: "Focus here", stepsText: "6 of 7 steps done right",
    lostText: "1 critical, 55 points lost", reviewText: null, provisional: false,
  });
  expect(state.flags).toEqual({
    countText: "1 critical", empty: false,
    cards: [{
      stepKey: "submit_and_confirm_transfer", title: "Submit and confirm transfer", pointsText: "\u221255 points",
      message: "Moved $114 savings \u2192 checking. The caller asked for checking \u2192 savings.", severity: "critical",
    }],
  });
});

test("the sample call shows its 9 turns, filler hidden, with the 0:33 and 0:44 labels", () => {
  const { transcript } = present(sample());
  expect(transcript.countText).toBe("9 turns, verbatim");
  expect(transcript.empty).toBe(false);
  expect(transcript.turns.map((t) => t.timeText)).toEqual(["0:02", "0:10", "0:21", "0:26", "0:33", "0:40", "0:44", "0:55", "0:57"]);
  const readBack = transcript.turns.find((t) => t.timeText === "0:33");
  expect(readBack).toMatchObject({ speakerLabel: "Agent", tone: "wrong", stepKeys: ["submit_and_confirm_transfer"] });
  const done = transcript.turns.find((t) => t.timeText === "0:44");
  expect(done?.tone).toBe("wrong");
  expect(done?.labels.map((l) => l.kind)).toEqual(["wrong", "evidence"]);
  expect(done?.labels[1].text).toBe("Evidence for Offer further help");
  expect(done?.stepKeys).toEqual(["submit_and_confirm_transfer", "offer_further_help"]);
  expect(transcript.turns.find((t) => t.timeText === "0:10")).toMatchObject({ speakerLabel: "Customer", tone: "plain", labels: [] });
});

test("a call with no score yet, still provisional, with points under review", () => {
  const detail = sample();
  const state = present({ ...detail, score: { ...detail.score, score: null, provisional: true, pointsUnderReview: 10 } });
  expect(state.score).toMatchObject({
    value: null, band: null, bandLabel: "Not scored yet", stepsText: "6 of 7 steps done right so far",
    reviewText: "10 points under review", provisional: true,
  });
});

test("nothing to show: no turns left and no flags", () => {
  const detail = sample();
  const state = present({ ...detail, turns: detail.turns.filter(isFillerTurn), flags: [] });
  expect(state.transcript).toEqual({ countText: "0 turns, verbatim", empty: true, turns: [] });
  expect(state.flags).toEqual({ countText: null, empty: true, cards: [] });
});

test("loading, not found and fail states", () => {
  const viewModel = new CallDetailViewModel();
  const presenter = new ViewCallDetailPresenter(viewModel);
  presenter.prepareNotFoundView();
  expect(viewModel.getState()).toEqual({ kind: "notFound", title: "Call not found", backHref: "/" });
  presenter.prepareFailView("GET /calls/1 failed (500)");
  expect(viewModel.getState()).toEqual({ kind: "error", title: "Couldn't load this call", message: "GET /calls/1 failed (500)" });
  presenter.prepareLoadingView();
  expect(viewModel.getState()).toEqual({ kind: "loading", message: LOADING_MESSAGE });
});
