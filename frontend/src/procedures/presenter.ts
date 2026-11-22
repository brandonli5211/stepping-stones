import type { ViewProceduresOutputBoundary } from "./outputBoundary";
import type { ViewProceduresOutputData } from "./outputData";
import { PROCEDURES_LOADING_MESSAGE, type ProceduresViewModel } from "./viewModel";

// Presenter: chooses a valid tab and shapes API values into exactly what the page draws.
export class ViewProceduresPresenter implements ViewProceduresOutputBoundary {
  constructor(private readonly viewModel: ProceduresViewModel) {}

  prepareLoadingView(): void { this.viewModel.setState({ kind: "loading", message: PROCEDURES_LOADING_MESSAGE }); }
  prepareFailView(message: string): void { this.viewModel.setState({ kind: "error", title: "Couldn't load procedures", message }); }

  prepareSuccessView(output: ViewProceduresOutputData): void {
    if (output.procedures.length === 0) {
      this.viewModel.setState({ kind: "empty", message: "No procedures are available yet" });
      return;
    }
    const selected = output.procedures.find((item) => item.callType === output.selectedCallType) ?? output.procedures[0];
    this.viewModel.setState({
      kind: "ready",
      tabs: output.procedures.map((item) => ({ callType: item.callType, name: item.name })),
      selectedCallType: selected.callType,
      name: selected.name,
      description: selected.description,
      steps: [...selected.steps].sort((left, right) => left.order - right.order).map((step) => ({ ...step })),
    });
  }
}
