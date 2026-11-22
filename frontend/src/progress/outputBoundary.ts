import type { ViewProgressOutputData } from "./outputData";

// Output Boundary for ViewProgress: what the use case may ask of a presenter.
export interface ViewProgressOutputBoundary {
  prepareLoadingView(): void;
  prepareSuccessView(output: ViewProgressOutputData): void;
  prepareFailView(message: string): void;
}
