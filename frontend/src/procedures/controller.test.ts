import { ViewProceduresController } from "./controller";
import { ViewProceduresInputData } from "./inputData";
import { ProceduresViewModel } from "./viewModel";

test("load sends the requested procedure from the address to the use case", async () => {
  const execute = vi.fn().mockResolvedValue(undefined);
  const controller = new ViewProceduresController({ execute }, new ProceduresViewModel());
  await controller.load("transfer_money");
  expect(execute).toHaveBeenCalledWith(new ViewProceduresInputData("transfer_money"));
});

test("selectProcedure delegates to the view model", () => {
  const viewModel = new ProceduresViewModel();
  const selectProcedure = vi.spyOn(viewModel, "selectProcedure").mockReturnValue(true);
  expect(new ViewProceduresController({ execute: vi.fn() }, viewModel).selectProcedure("replace_card")).toBe(true);
  expect(selectProcedure).toHaveBeenCalledWith("replace_card");
});
