import type { ViewProceduresOutputData } from "./outputData";

export interface ViewProceduresOutputBoundary {
  prepareLoadingView(): void;
  prepareSuccessView(output: ViewProceduresOutputData): void;
  prepareFailView(message: string): void;
}
