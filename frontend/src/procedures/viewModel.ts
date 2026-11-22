export type ProcedureTabView = { callType: string; name: string };
export type ProcedureStepView = { key: string; order: number; name: string; description: string };
export type ProcedureView = { callType: string; name: string; description: string; steps: ProcedureStepView[] };

export type ProceduresViewState =
  | { kind: "loading"; message: string }
  | { kind: "error"; title: string; message: string }
  | { kind: "empty"; message: string }
  | { kind: "ready"; procedures: ProcedureView[]; selectedCallType: string; name: string; description: string; steps: ProcedureStepView[] };

export const PROCEDURES_LOADING_MESSAGE = "Loading procedures…";

export class ProceduresViewModel {
  private state: ProceduresViewState = { kind: "loading", message: PROCEDURES_LOADING_MESSAGE };
  private readonly listeners = new Set<() => void>();

  getState = (): ProceduresViewState => this.state;
  setState = (state: ProceduresViewState): void => { this.state = state; this.listeners.forEach((listener) => listener()); };
  selectProcedure = (callType: string): boolean => {
    if (this.state.kind !== "ready" || callType === this.state.selectedCallType) return false;
    const procedure = this.state.procedures.find((item) => item.callType === callType);
    if (!procedure) return false;
    this.setState({ ...this.state, selectedCallType: procedure.callType, name: procedure.name, description: procedure.description, steps: procedure.steps });
    return true;
  };
  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  };
}
