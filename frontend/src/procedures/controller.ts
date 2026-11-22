import type { ViewProceduresInputBoundary } from "./inputBoundary";
import { ViewProceduresInputData } from "./inputData";

// Controller: converts a selected tab into the query parameter the page can restore after reload.
export class ViewProceduresController {
  constructor(private readonly useCase: ViewProceduresInputBoundary) {}

  load(selectedCallType: string | null): Promise<void> { return this.useCase.execute(new ViewProceduresInputData(selectedCallType)); }
}
