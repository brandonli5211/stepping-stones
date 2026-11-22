import { fireEvent, render, screen } from "@testing-library/react";
import ProceduresPage from "./ProceduresPage";
import { ViewProceduresPresenter } from "./presenter";
import { ViewProceduresOutputData } from "./outputData";
import { ProceduresViewModel } from "./viewModel";
import type { ViewProceduresController } from "./controller";

test("draws a selected procedure and saves the selected tab in the URL", async () => {
  const viewModel = new ProceduresViewModel();
  const controller = { load: vi.fn().mockResolvedValue(undefined), selectProcedure: vi.fn().mockReturnValue(true) };
  render(<ProceduresPage viewModel={viewModel} controller={controller as unknown as ViewProceduresController} selectedCallType="transfer_money" />);
  new ViewProceduresPresenter(viewModel).prepareSuccessView(new ViewProceduresOutputData([
    { callType: "transfer_money", name: "Transfer money", description: "Move money", steps: [{ key: "greet", order: 1, name: "Greet", description: "Say hello" }] },
    { callType: "replace_card", name: "Replace card", description: "Replace it", steps: [] },
  ], "transfer_money"));
  expect(await screen.findByText("Greet")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Replace card" }));
  expect(window.location.search).toBe("?task=replace_card");
  expect(controller.load).toHaveBeenCalledTimes(1);
  expect(controller.selectProcedure).toHaveBeenCalledWith("replace_card");
});
