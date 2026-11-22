import type { ViewProceduresInputBoundary } from "./inputBoundary";
import { ViewProceduresInputData } from "./inputData";
import type { ProceduresViewModel } from "./viewModel";

// Controller: converts a selected tab into the query parameter the page can restore after reload.
export class ViewProceduresController {
  constructor(private readonly useCase: ViewProceduresInputBoundary, private readonly viewModel: ProceduresViewModel) {}

  load(selectedCallType: string | null): Promise<void> { return this.useCase.execute(new ViewProceduresInputData(selectedCallType)); }
  selectProcedure(callType: string): boolean { return this.viewModel.selectProcedure(callType); }
}
