import type { Procedure } from "./entities";

export interface ProceduresDataAccess {
  getProcedures(): Promise<Procedure[]>;
}
