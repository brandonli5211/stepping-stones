import type { ViewCallDetailInputData } from "./inputData";

// Input Boundary for ViewCallDetail: what a controller may ask of the use case.
export interface ViewCallDetailInputBoundary {
  execute(input: ViewCallDetailInputData): Promise<void>;
}
