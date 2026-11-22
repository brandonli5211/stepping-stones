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
