import type { ViewCallDetailOutputData } from "./outputData";

// Output Boundary for ViewCallDetail: what the use case may ask of a presenter.
export interface ViewCallDetailOutputBoundary {
  prepareLoadingView(): void;
  prepareSuccessView(output: ViewCallDetailOutputData): void;
  prepareNotFoundView(): void;
  prepareFailView(message: string): void;
}
