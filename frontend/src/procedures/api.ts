import type { ApiGateway } from "../application";
import type { ProceduresDataAccess } from "./dataAccess";
import type { Procedure } from "./entities";

export type ProceduresDto = { procedures: { call_type: string; name: string; description: string; steps: { key: string; order: number; step_name: string; step_description: string }[] }[] };

// Data access adapter for GET /procedures. It is the only place that knows API field names.
export class ProceduresApi implements ProceduresDataAccess {
  constructor(private readonly gateway: ApiGateway) {}

  async getProcedures(): Promise<Procedure[]> {
    return this.toProcedures(await this.gateway.get<ProceduresDto>("/procedures"));
  }

  toProcedures(dto: ProceduresDto): Procedure[] {
    return dto.procedures.map((procedure) => ({
      callType: procedure.call_type,
      name: procedure.name,
      description: procedure.description,
      steps: procedure.steps.map((step) => ({ key: step.key, order: step.order, name: step.step_name, description: step.step_description })),
    }));
  }
}
