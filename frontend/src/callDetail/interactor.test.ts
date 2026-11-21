import type { CallDetail } from "./entities";
import { ViewCallDetailInputData } from "./inputData";
import { ViewCallDetailInteractor } from "./interactor";
import type { ViewCallDetailOutputBoundary } from "./outputBoundary";
import type { ViewCallDetailOutputData } from "./outputData";

const DETAIL: CallDetail = {
  callId: 1, externalId: "a2f086d27b3a4f96", callTypeName: "Transfer money", summary: null,
  score: { score: 45, outOf: 100, stepsDoneRight: 6, stepsTotal: 7, pointsLost: 55, criticalCount: 1, pointsUnderReview: 0, provisional: false },
  turns: [], flags: [],
};

class Presenter implements ViewCallDetailOutputBoundary {
  calls: string[] = [];
  output: ViewCallDetailOutputData | null = null;
  prepareLoadingView() { this.calls.push("loading"); }
  prepareSuccessView(output: ViewCallDetailOutputData) { this.calls.push("success"); this.output = output; }
  prepareNotFoundView() { this.calls.push("notFound"); }
  prepareFailView(message: string) { this.calls.push(`fail:${message}`); }
}

const run = async (getCallDetail: (id: number) => Promise<CallDetail | null>) => {
  const presenter = new Presenter();
  await new ViewCallDetailInteractor({ getCallDetail }, presenter).execute(new ViewCallDetailInputData(1));
  return presenter;
};

test("a stored call goes to the presenter after the loading view", async () => {
  const getCallDetail = vi.fn().mockResolvedValue(DETAIL);
  const presenter = await run(getCallDetail);
  expect(getCallDetail).toHaveBeenCalledWith(1);
  expect(presenter.calls).toEqual(["loading", "success"]);
  expect(presenter.output?.detail).toBe(DETAIL);
});

test("no such call shows not found", async () => {
  expect((await run(async () => null)).calls).toEqual(["loading", "notFound"]);
});

test("a failure passes its message on", async () => {
  expect((await run(async () => { throw new Error("GET /calls/1 failed (500)"); })).calls)
    .toEqual(["loading", "fail:GET /calls/1 failed (500)"]);
  expect((await run(async () => { throw "boom"; })).calls).toEqual(["loading", "fail:Unknown error"]);
});

test("an answer to an older request is dropped", async () => {
  let resolveFirst: (d: CallDetail) => void = () => {};
  const first = new Promise<CallDetail>((resolve) => { resolveFirst = resolve; });
  const getCallDetail = vi.fn().mockReturnValueOnce(first).mockResolvedValueOnce(null);
  const presenter = new Presenter();
  const interactor = new ViewCallDetailInteractor({ getCallDetail }, presenter);
  const older = interactor.execute(new ViewCallDetailInputData(1));
  await interactor.execute(new ViewCallDetailInputData(2));
  resolveFirst(DETAIL);
  await older;
  expect(presenter.calls).toEqual(["loading", "loading", "notFound"]);
});

test("input and output data keep what they are given", () => {
  expect(new ViewCallDetailInputData(7).callId).toBe(7);
});
