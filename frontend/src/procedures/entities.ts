// What the app knows about a procedure. The server owns the text and ordering.
export type ProcedureStep = { key: string; order: number; name: string; description: string };

export type Procedure = { callType: string; name: string; description: string; steps: ProcedureStep[] };
