import { ViewProceduresInteractor } from "./interactor";
import { ViewProceduresInputData } from "./inputData";

test("presents loading then loaded procedures", async () => {
  const presenter = { prepareLoadingView: vi.fn(), prepareSuccessView: vi.fn(), prepareFailView: vi.fn() };
  await new ViewProceduresInteractor({ getProcedures: vi.fn().mockResolvedValue([]) }, presenter).execute(new ViewProceduresInputData(null));
  expect(presenter.prepareLoadingView).toHaveBeenCalledOnce();
  expect(presenter.prepareSuccessView).toHaveBeenCalledOnce();
});

test("presents failures", async () => {
  const presenter = { prepareLoadingView: vi.fn(), prepareSuccessView: vi.fn(), prepareFailView: vi.fn() };
  await new ViewProceduresInteractor({ getProcedures: vi.fn().mockRejectedValue(new Error("offline")) }, presenter).execute(new ViewProceduresInputData(null));
  expect(presenter.prepareFailView).toHaveBeenCalledWith("offline");
});

test("drops an older answer when a newer load finishes first", async () => {
  let firstDone: (value: []) => void;
  let secondDone: (value: []) => void;
  const getProcedures = vi.fn()
    .mockImplementationOnce(() => new Promise<[]>(resolve => { firstDone = resolve; }))
    .mockImplementationOnce(() => new Promise<[]>(resolve => { secondDone = resolve; }));
  const presenter = { prepareLoadingView: vi.fn(), prepareSuccessView: vi.fn(), prepareFailView: vi.fn() };
  const interactor = new ViewProceduresInteractor({ getProcedures }, presenter);
  const first = interactor.execute(new ViewProceduresInputData("transfer_money"));
  const second = interactor.execute(new ViewProceduresInputData("replace_card"));
  secondDone!([]);
  await second;
  firstDone!([]);
  await first;
  expect(presenter.prepareSuccessView).toHaveBeenCalledTimes(1);
  expect(presenter.prepareSuccessView.mock.calls[0][0].selectedCallType).toBe("replace_card");
});
