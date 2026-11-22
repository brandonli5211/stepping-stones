import type { ApiGateway } from "../application";
import { ProceduresApi } from "./api";
import { ViewProceduresController } from "./controller";
import { ViewProceduresInteractor } from "./interactor";
import { ViewProceduresPresenter } from "./presenter";
import { ProceduresViewModel } from "./viewModel";

export function parseProcedureType(search: string): string | null {
  const task = new URLSearchParams(search).get("task");
  return task && /^[a-z][a-z0-9_]*$/.test(task) ? task : null;
}

export function createProceduresScreen(gateway: ApiGateway) {
  const viewModel = new ProceduresViewModel();
  const interactor = new ViewProceduresInteractor(new ProceduresApi(gateway), new ViewProceduresPresenter(viewModel));
  return { viewModel, controller: new ViewProceduresController(interactor) };
}
