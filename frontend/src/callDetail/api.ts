import { ApiError, type ApiGateway } from "../application";
import type { CallDetailDataAccess } from "./dataAccess";
import type { CallDetail, Note, Severity } from "./entities";

// The body of GET /calls/{id}, as the server sends it (docs/api-contract.md). Only the parts this page draws;
// steps and type_details are left for the steps panel. These names stay in this file.
export type CallDetailDto = {
  header: { call_id: number; external_id: string; call_type: string; call_type_name: string; summary: string | null };
  score: {
    score: number | null; out_of: number; steps_done_right: number; steps_total: number; points_lost: number;
    critical_count: number; points_under_review: number; provisional: boolean;
  };
  transcript: {
    idx: number; speaker: "agent" | "caller"; start_seconds: number | null; text: string;
    notes: { kind: string; step_key: string; text: string }[];
  }[];
  flags: {
    step_key: string; step_name: string; status: "missed" | "wrong"; severity: Severity;
    points_lost: number; message: string | null;
  }[];
};

const NOTE_KINDS = new Set<string>(["evidence", "wrong"]);

// The typed gateway for one call: the Data Access Interface over the shell's ApiGateway.
export class CallDetailApi implements CallDetailDataAccess {
  constructor(private readonly gateway: ApiGateway) {}

  async getCallDetail(callId: number): Promise<CallDetail | null> {
    try {
      return this.toCallDetail(await this.gateway.get<CallDetailDto>(this.callDetailPath(callId)));
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  }

  callDetailPath(callId: number): string {
    return `/calls/${callId}`;
  }

  toCallDetail(dto: CallDetailDto): CallDetail {
    return {
      callId: dto.header.call_id,
      externalId: dto.header.external_id,
      callTypeName: dto.header.call_type_name,
      summary: dto.header.summary,
      score: {
        score: dto.score.score, outOf: dto.score.out_of, stepsDoneRight: dto.score.steps_done_right,
        stepsTotal: dto.score.steps_total, pointsLost: dto.score.points_lost, criticalCount: dto.score.critical_count,
        pointsUnderReview: dto.score.points_under_review, provisional: dto.score.provisional,
      },
      turns: dto.transcript.map((t) => ({
        idx: t.idx, speaker: t.speaker, startSeconds: t.start_seconds, text: t.text,
        // a note kind this page doesn't know is left off, so the turn shows plain
        notes: t.notes
          .filter((n) => NOTE_KINDS.has(n.kind))
          .map((n): Note => ({ kind: n.kind as Note["kind"], stepKey: n.step_key, text: n.text })),
      })),
      flags: dto.flags.map((f) => ({
        stepKey: f.step_key, stepName: f.step_name, status: f.status, severity: f.severity,
        pointsLost: f.points_lost, message: f.message,
      })),
    };
  }
}
