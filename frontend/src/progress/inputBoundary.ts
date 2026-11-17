import type { ViewProgressInputData } from "./inputData";

// Input Boundary for ViewProgress: what a controller may ask of the use case.
export interface ViewProgressInputBoundary {
  execute(input: ViewProgressInputData): Promise<void>;
}
