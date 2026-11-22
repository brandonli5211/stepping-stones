import { ProceduresViewModel, PROCEDURES_LOADING_MESSAGE } from "./viewModel";

const ready = {
  kind: "ready" as const,
  procedures: [
    { callType: "transfer_money", name: "Transfer money", description: "Move", steps: [] },
    { callType: "replace_card", name: "Replace card", description: "Replace", steps: [] },
  ],
  selectedCallType: "transfer_money",
  name: "Transfer money",
  description: "Move",
  steps: [],
};

test("starts loading and notifies subscribers for a valid selection", () => {
  const viewModel = new ProceduresViewModel();
  expect(viewModel.getState()).toEqual({ kind: "loading", message: PROCEDURES_LOADING_MESSAGE });
  const listener = vi.fn();
  viewModel.subscribe(listener);
  viewModel.setState(ready);
  expect(viewModel.selectProcedure("replace_card")).toBe(true);
  expect(viewModel.getState()).toMatchObject({ selectedCallType: "replace_card", name: "Replace card" });
  expect(listener).toHaveBeenCalledTimes(2);
});

test("does not notify for an unchanged or unknown selection", () => {
  const viewModel = new ProceduresViewModel();
  viewModel.setState(ready);
  const listener = vi.fn();
  viewModel.subscribe(listener);
  expect(viewModel.selectProcedure("transfer_money")).toBe(false);
  expect(viewModel.selectProcedure("not_real")).toBe(false);
  expect(listener).not.toHaveBeenCalled();
});
