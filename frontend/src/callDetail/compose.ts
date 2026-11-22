import type { ApiGateway } from "../application";
import { CallDetailApi } from "./api";
import { ViewCallDetailController } from "./controller";
import type { CallDetailDataAccess } from "./dataAccess";
import { ViewCallDetailInteractor } from "./interactor";
import { ViewCallDetailPresenter } from "./presenter";
import { CallDetailViewModel } from "./viewModel";

// the id from /calls/{id} as a whole number of 1 or more, otherwise no call
export function parseCallId(value: string | null | undefined): number | null {
  return value != null && /^[1-9]\d*$/.test(value) ? Number(value) : null;
}

// an id that can't be a call is answered "not found" here, so no request is sent for it
const NO_SUCH_CALL: CallDetailDataAccess = { getCallDetail: async () => null };

// builds the ViewCallDetail parts for one call: the page gets the view model to draw and the controller to call
export function createCallDetailScreen(gateway: ApiGateway, callId: number | null) {
  const viewModel = new CallDetailViewModel();
  const dataAccess = callId == null ? NO_SUCH_CALL : new CallDetailApi(gateway);
  const interactor = new ViewCallDetailInteractor(dataAccess, new ViewCallDetailPresenter(viewModel));
  return { viewModel, controller: new ViewCallDetailController(interactor, callId ?? 0, viewModel) };
}
