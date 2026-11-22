import type { ProceduresDataAccess } from "./dataAccess";
import type { ViewProceduresInputBoundary } from "./inputBoundary";
import type { ViewProceduresInputData } from "./inputData";
import type { ViewProceduresOutputBoundary } from "./outputBoundary";
import { ViewProceduresOutputData } from "./outputData";

export class ViewProceduresInteractor implements ViewProceduresInputBoundary {
  constructor(private readonly dataAccess: ProceduresDataAccess, private readonly presenter: ViewProceduresOutputBoundary) {}

  async execute(input: ViewProceduresInputData): Promise<void> {
    this.presenter.prepareLoadingView();
    try {
      this.presenter.prepareSuccessView(new ViewProceduresOutputData(await this.dataAccess.getProcedures(), input.selectedCallType));
    } catch (error) {
      this.presenter.prepareFailView(error instanceof Error ? error.message : "Unknown error");
    }
  }
}
