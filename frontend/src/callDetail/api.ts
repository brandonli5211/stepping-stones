import { ApiError, type ApiGateway } from "../application";
import type { CallDetailDataAccess } from "./dataAccess";
import type { CallDetail, FieldResult, FieldRow, Note, Severity, Step, StepStatus, SubCheck, SubCheckResult, TypeDetails } from "./entities";

// The body of GET /calls/{id}, as the server sends it (docs/api-contract.md). Snake_case names stay in this file.
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
  steps: {
    key: string; position: number; name: string; status: string; severity: Severity;
    points: number; points_lost: number; points_under_review: number;
    details: {
      description: string | null; detail: string | null;
      sub_checks: { key: string; description: string; points: number; result: string }[];
      evidence: { quote: string; turn_idx: number; start_seconds: number | null } | null;
      coaching: string | null;
    };
  }[];
  flags: {
    step_key: string; step_name: string; status: "missed" | "wrong"; severity: Severity;
    points_lost: number; message: string | null;
  }[];
  type_details: {
    type: string;
    fields?: { field: string; label: string; caller_asked: string | null; logged: string | null; result: string }[];
  };
};

const NOTE_KINDS = new Set<string>(["evidence", "wrong"]);
const STEP_STATUSES = new Set<string>(["completed", "missed", "wrong", "under_review"]);
const SUB_RESULTS = new Set<string>(["passed", "failed", "under_review"]);
const FIELD_RESULTS = new Set<string>(["match", "mismatch", "reversed"]);

// a step, sub-check or field result this page doesn't know is left off, so the page never invents one
export function toStep(dto: CallDetailDto["steps"][number]): Step | null {
  if (!STEP_STATUSES.has(dto.status)) return null;
  const subChecks: SubCheck[] = dto.details.sub_checks.flatMap((check) => (
    SUB_RESULTS.has(check.result)
      ? [{ key: check.key, description: check.description, points: check.points, result: check.result as SubCheckResult }]
      : []
  ));
  return {
    key: dto.key, position: dto.position, name: dto.name, status: dto.status as StepStatus, severity: dto.severity,
    points: dto.points, pointsLost: dto.points_lost, pointsUnderReview: dto.points_under_review,
    description: dto.details.description, detail: dto.details.detail, subChecks,
    evidence: dto.details.evidence && {
      quote: dto.details.evidence.quote, turnIdx: dto.details.evidence.turn_idx, startSeconds: dto.details.evidence.start_seconds,
    },
    coaching: dto.details.coaching,
  };
}

export function toTypeDetails(dto: CallDetailDto["type_details"]): TypeDetails {
  if (dto.type !== "transfer_money" || !dto.fields) return { type: dto.type, fields: [] };
  const fields: FieldRow[] = dto.fields.flatMap((row) => (
    FIELD_RESULTS.has(row.result)
      ? [{ field: row.field, label: row.label, callerAsked: row.caller_asked, logged: row.logged, result: row.result as FieldResult }]
      : []
  ));
  return { type: "transfer_money", fields };
}

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
      callType: dto.header.call_type,
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
      steps: dto.steps.flatMap((step) => {
        const mapped = toStep(step);
        return mapped ? [mapped] : [];
      }),
      flags: dto.flags.map((f) => ({
        stepKey: f.step_key, stepName: f.step_name, status: f.status, severity: f.severity,
        pointsLost: f.points_lost, message: f.message,
      })),
      typeDetails: toTypeDetails(dto.type_details),
    };
  }
}
