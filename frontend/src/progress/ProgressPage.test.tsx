import { act, render, screen } from "@testing-library/react";
import type { ViewProgressController } from "./controller";
import { ViewProgressPresenter } from "./presenter";
import ProgressPage from "./ProgressPage";
import { ProgressViewModel } from "./viewModel";

test("progress error state", () => {
  const viewModel = new ProgressViewModel();
  const load = vi.fn().mockResolvedValue(undefined);
  render(<ProgressPage viewModel={viewModel} controller={{ load } as unknown as ViewProgressController} />);
  act(() => new ViewProgressPresenter(viewModel).prepareFailView("GET /progress failed (503)"));

  expect(load).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("alert").textContent).toContain("Couldn't load your progress");
  expect(screen.getByRole("alert").textContent).toContain("GET /progress failed (503)");
  expect(screen.queryAllByTestId("week-bar")).toHaveLength(0);
  expect(screen.queryByText("Demo data")).toBeNull();
});
