import type { Procedure } from "./entities";

export class ViewProceduresOutputData {
  constructor(readonly procedures: Procedure[], readonly selectedCallType: string | null) {}
}
