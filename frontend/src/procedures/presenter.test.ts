import { ViewProceduresOutputData } from "./outputData";
import { ViewProceduresPresenter } from "./presenter";
import { ProceduresViewModel } from "./viewModel";

const procedures = [
  { callType: "transfer_money", name: "Transfer money", description: "Move money", steps: [{ key: "second", order: 2, name: "Second", description: "" }, { key: "first", order: 1, name: "First", description: "" }] },
  { callType: "replace_card", name: "Replace card", description: "Replace it", steps: [] },
];

test("selects the requested procedure and orders its steps", () => {
  const viewModel = new ProceduresViewModel();
  new ViewProceduresPresenter(viewModel).prepareSuccessView(new ViewProceduresOutputData(procedures, "transfer_money"));
  expect(viewModel.getState()).toMatchObject({ kind: "ready", selectedCallType: "transfer_money", name: "Transfer money", steps: [{ name: "First" }, { name: "Second" }] });
});

test("falls back to the first returned procedure", () => {
  const viewModel = new ProceduresViewModel();
  new ViewProceduresPresenter(viewModel).prepareSuccessView(new ViewProceduresOutputData(procedures, "not_real"));
  expect(viewModel.getState()).toMatchObject({ kind: "ready", selectedCallType: "transfer_money" });
});
