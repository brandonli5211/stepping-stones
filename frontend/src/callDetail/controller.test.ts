import { ViewCallDetailController } from "./controller";
import { ViewCallDetailInputData } from "./inputData";
import { CallDetailViewModel } from "./viewModel";

test("load() asks the use case for this call", async () => {
  const execute = vi.fn().mockResolvedValue(undefined);
  await new ViewCallDetailController({ execute }, 7, new CallDetailViewModel()).load();
  expect(execute).toHaveBeenCalledWith(new ViewCallDetailInputData(7));
});

test("selectStep() sets and clears the selected step", () => {
  const viewModel = new CallDetailViewModel();
  const controller = new ViewCallDetailController({ execute: vi.fn() }, 7, viewModel);
  controller.selectStep("submit_and_confirm_transfer");
  expect(viewModel.selectedStepKey()).toBe("submit_and_confirm_transfer");
  controller.selectStep(null);
  expect(viewModel.selectedStepKey()).toBeNull();
});
