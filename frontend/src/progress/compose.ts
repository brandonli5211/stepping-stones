import type { ApiGateway } from "../application";
import { ProgressApi } from "./api";
import { ViewProgressController } from "./controller";
import { ViewProgressInteractor } from "./interactor";
import { ViewProgressPresenter } from "./presenter";
import { ProgressViewModel } from "./viewModel";

// the agent setting as a whole number of 1 or more, otherwise no agent
export function parseAgentId(value: string | undefined): number | null {
  return value != null && /^[1-9]\d*$/.test(value.trim()) ? Number(value.trim()) : null;
}

// builds the ViewProgress parts once: the page gets the view model to draw and the controller to call
export function createProgressScreen(gateway: ApiGateway, agentId: number | null) {
  const viewModel = new ProgressViewModel();
  const interactor = new ViewProgressInteractor(new ProgressApi(gateway), new ViewProgressPresenter(viewModel));
  return { viewModel, controller: new ViewProgressController(interactor, agentId) };
}
