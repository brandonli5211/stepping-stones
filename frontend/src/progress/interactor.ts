import type { ProgressDataAccess } from "./dataAccess";
import type { ViewProgressInputBoundary } from "./inputBoundary";
import type { ViewProgressInputData } from "./inputData";
import type { ViewProgressOutputBoundary } from "./outputBoundary";
import { ViewProgressOutputData } from "./outputData";

// Interactor for ViewProgress: load the agent's progress and hand it, or a loading or failure notice, to the presenter.
export class ViewProgressInteractor implements ViewProgressInputBoundary {
  private latestRequest = 0;

  constructor(
    private readonly dataAccess: ProgressDataAccess,
    private readonly presenter: ViewProgressOutputBoundary,
  ) {}

  async execute(input: ViewProgressInputData): Promise<void> {
    const request = ++this.latestRequest;
    this.presenter.prepareLoadingView();
    try {
      const progress = await this.dataAccess.getProgress(input.agentId);
      // an answer to an older request is dropped
      if (request === this.latestRequest) this.presenter.prepareSuccessView(new ViewProgressOutputData(progress));
    } catch (error) {
      if (request === this.latestRequest) {
        this.presenter.prepareFailView(error instanceof Error ? error.message : "Unknown error");
      }
    }
  }
}
