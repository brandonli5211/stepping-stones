import type { ViewCallDetailInputBoundary } from "./inputBoundary";
import { ViewCallDetailInputData } from "./inputData";
import type { CallDetailViewModel } from "./viewModel";

// Controller for ViewCallDetail: turns "the agent opened this call" into input data for the use case,
// and "the agent chose a step" into the shared selection (#36 calls the same method).
export class ViewCallDetailController {
  constructor(
    private readonly useCase: ViewCallDetailInputBoundary,
    private readonly callId: number,
    private readonly viewModel: CallDetailViewModel,
  ) {}

  load(): Promise<void> {
    return this.useCase.execute(new ViewCallDetailInputData(this.callId));
  }

  selectStep(stepKey: string | null): void {
    this.viewModel.selectStep(stepKey);
  }
}
