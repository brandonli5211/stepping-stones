import type { CallDetailDataAccess } from "./dataAccess";
import type { ViewCallDetailInputBoundary } from "./inputBoundary";
import type { ViewCallDetailInputData } from "./inputData";
import type { ViewCallDetailOutputBoundary } from "./outputBoundary";
import { ViewCallDetailOutputData } from "./outputData";

// Interactor for ViewCallDetail: load one stored call and hand it, or a loading, not-found or failure notice, to the presenter.
export class ViewCallDetailInteractor implements ViewCallDetailInputBoundary {
  private latestRequest = 0;

  constructor(
    private readonly dataAccess: CallDetailDataAccess,
    private readonly presenter: ViewCallDetailOutputBoundary,
  ) {}

  async execute(input: ViewCallDetailInputData): Promise<void> {
    const request = ++this.latestRequest;
    this.presenter.prepareLoadingView();
    try {
      const detail = await this.dataAccess.getCallDetail(input.callId);
      // an answer to an older request is dropped
      if (request !== this.latestRequest) return;
      if (detail == null) this.presenter.prepareNotFoundView();
      else this.presenter.prepareSuccessView(new ViewCallDetailOutputData(detail));
    } catch (error) {
      if (request === this.latestRequest) {
        this.presenter.prepareFailView(error instanceof Error ? error.message : "Unknown error");
      }
    }
  }
}
