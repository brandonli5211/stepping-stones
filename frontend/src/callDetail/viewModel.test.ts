import { CallDetailViewModel, LOADING_MESSAGE } from "./viewModel";

test("starts loading with nothing selected", () => {
  const viewModel = new CallDetailViewModel();
  expect(viewModel.getState()).toEqual({ kind: "loading", message: LOADING_MESSAGE });
  expect(viewModel.selectedStepKey()).toBeNull();
});

test("tells subscribers when the state changes", () => {
  const viewModel = new CallDetailViewModel();
  const listener = vi.fn();
  viewModel.subscribe(listener);
  viewModel.setState({ kind: "notFound", title: "Call not found", backHref: "/" });
  expect(listener).toHaveBeenCalledTimes(1);
  expect(viewModel.getState().kind).toBe("notFound");
});

test("tells subscribers when the selected step changes, and not when it stays the same", () => {
  const viewModel = new CallDetailViewModel();
  const listener = vi.fn();
  viewModel.subscribe(listener);
  viewModel.selectStep("submit_and_confirm_transfer");
  viewModel.selectStep("submit_and_confirm_transfer");
  expect(viewModel.selectedStepKey()).toBe("submit_and_confirm_transfer");
  expect(listener).toHaveBeenCalledTimes(1);
  viewModel.selectStep(null);
  expect(viewModel.selectedStepKey()).toBeNull();
  expect(listener).toHaveBeenCalledTimes(2);
});

test("an unsubscribed listener is no longer told", () => {
  const viewModel = new CallDetailViewModel();
  const listener = vi.fn();
  viewModel.subscribe(listener)();
  viewModel.selectStep("greet_and_open");
  expect(listener).not.toHaveBeenCalled();
});
