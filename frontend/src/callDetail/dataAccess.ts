import type { CallDetail } from "./entities";

// Data Access Interface for ViewCallDetail.
export interface CallDetailDataAccess {
  // Resolves to null when no call has this id. Rejects with an Error when the call cannot be loaded.
  getCallDetail(callId: number): Promise<CallDetail | null>;
}
