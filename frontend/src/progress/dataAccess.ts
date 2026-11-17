import type { Progress } from "./entities";

// Data Access Interface for ViewProgress.
export interface ProgressDataAccess {
  // Rejects with an Error when the progress cannot be loaded.
  getProgress(agentId: number | null): Promise<Progress>;
}
