import type { ApiGateway } from "../application";
import type { ProgressDataAccess } from "./dataAccess";
import type { Progress } from "./entities";

// The body of GET /progress, exactly as the server sends it. These names stay in this file.
export type ProgressDto = {
  demo_data: boolean;
  weeks: { week_start: string; steps_completed: number; steps_total: number; percent: number | null; is_current: boolean }[];
  this_week: { steps_completed: number; steps_total: number; percent: number | null } | null;
  first_week_percent: number | null;
  comparison: string | null;
  call_types: { call_type: string; name: string; steps_completed: number; steps_total: number; percent: number | null; calls: number }[];
  steps: {
    step_key: string; name: string; call_type: string | null; label: string;
    results: string[]; misses: number; window: number; summary: string;
  }[];
};

// The typed gateway for progress: the Data Access Interface over the shell's ApiGateway.
export class ProgressApi implements ProgressDataAccess {
  constructor(private readonly gateway: ApiGateway) {}

  async getProgress(agentId: number | null): Promise<Progress> {
    return this.toProgress(await this.gateway.get<ProgressDto>(this.progressPath(agentId)));
  }

  progressPath(agentId: number | null): string {
    return agentId == null ? "/progress" : `/progress?agent_id=${agentId}`;
  }

  toProgress(dto: ProgressDto): Progress {
    return {
      demoData: dto.demo_data,
      weeks: dto.weeks.map((w) => ({
        weekStart: w.week_start, stepsCompleted: w.steps_completed, stepsTotal: w.steps_total,
        percent: w.percent, isCurrent: w.is_current,
      })),
      thisWeek: dto.this_week && {
        stepsCompleted: dto.this_week.steps_completed, stepsTotal: dto.this_week.steps_total, percent: dto.this_week.percent,
      },
      firstWeekPercent: dto.first_week_percent,
      comparison: dto.comparison,
      callTypes: dto.call_types.map((t) => ({
        callType: t.call_type, name: t.name, stepsCompleted: t.steps_completed, stepsTotal: t.steps_total,
        percent: t.percent, calls: t.calls,
      })),
      steps: dto.steps.map((s) => ({
        stepKey: s.step_key, name: s.name, callType: s.call_type, label: s.label,
        results: [...s.results], misses: s.misses, window: s.window, summary: s.summary,
      })),
    };
  }
}
