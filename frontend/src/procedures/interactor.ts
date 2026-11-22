import type { ProceduresDataAccess } from "./dataAccess";
import type { ViewProceduresInputBoundary } from "./inputBoundary";
import type { ViewProceduresInputData } from "./inputData";
import type { ViewProceduresOutputBoundary } from "./outputBoundary";
import { ViewProceduresOutputData } from "./outputData";

export class ViewProceduresInteractor implements ViewProceduresInputBoundary {
  private latestRequest = 0;
  constructor(private readonly dataAccess: ProceduresDataAccess, private readonly presenter: ViewProceduresOutputBoundary) {}

  async execute(input: ViewProceduresInputData): Promise<void> {
    const request = ++this.latestRequest;
    this.presenter.prepareLoadingView();
    try {
      const procedures = await this.dataAccess.getProcedures();
      if (request === this.latestRequest) this.presenter.prepareSuccessView(new ViewProceduresOutputData(procedures, input.selectedCallType));
    } catch (error) {
      if (request === this.latestRequest) this.presenter.prepareFailView(error instanceof Error ? error.message : "Unknown error");
    }
  }
}
