import type { ViewProgressInputBoundary } from "./inputBoundary";
import { ViewProgressInputData } from "./inputData";

// Controller for ViewProgress: turns "the agent opened Progress" into input data for the use case.
export class ViewProgressController {
  constructor(
    private readonly useCase: ViewProgressInputBoundary,
    private readonly agentId: number | null,
  ) {}

  load(): Promise<void> {
    return this.useCase.execute(new ViewProgressInputData(this.agentId));
  }
}
