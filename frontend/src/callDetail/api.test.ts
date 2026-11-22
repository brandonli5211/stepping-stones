import { ApiError } from "../application";
import { SAMPLE_CALL_DETAIL } from "../sampleCallDetail";
import { CallDetailApi, type CallDetailDto } from "./api";

const SAMPLE = SAMPLE_CALL_DETAIL as unknown as CallDetailDto;
const gatewayAnswering = (get: (path: string) => Promise<unknown>) => ({ get: get as <T>(path: string) => Promise<T> });

test("asks for /calls/{id}", async () => {
  const get = vi.fn().mockResolvedValue(SAMPLE);
  await new CallDetailApi(gatewayAnswering(get)).getCallDetail(1);
  expect(get).toHaveBeenCalledWith("/calls/1");
  expect(new CallDetailApi(gatewayAnswering(get)).callDetailPath(42)).toBe("/calls/42");
});

test("maps the server's answer to the call detail", async () => {
  const detail = await new CallDetailApi(gatewayAnswering(async () => SAMPLE)).getCallDetail(1);
  expect(detail?.callTypeName).toBe("Transfer money");
  expect(detail?.externalId).toBe("a2f086d27b3a4f96");
  expect(detail?.score).toEqual({
    score: 45, outOf: 100, stepsDoneRight: 6, stepsTotal: 7, pointsLost: 55, criticalCount: 1,
    pointsUnderReview: 0, provisional: false,
  });
  expect(detail?.turns).toHaveLength(16);
  const readBack = detail?.turns.find((t) => t.idx === 9);
  expect(readBack).toMatchObject({ speaker: "agent", startSeconds: 33.53 });
  expect(readBack?.notes).toEqual([
    { kind: "wrong", stepKey: "submit_and_confirm_transfer", text: "Wrong: read back reversed. The caller asked checking → savings" },
  ]);
  expect(detail?.flags).toEqual([{
    stepKey: "submit_and_confirm_transfer", stepName: "Submit and confirm transfer", status: "wrong",
    severity: "critical", pointsLost: 55, message: "Moved $114 savings → checking. The caller asked for checking → savings.",
  }]);
  expect(detail?.callType).toBe("transfer_money");
  expect(detail?.steps).toHaveLength(7);
  const confirm = detail?.steps.find((step) => step.key === "submit_and_confirm_transfer");
  expect(confirm).toMatchObject({
    status: "wrong", pointsLost: 55, severity: "critical",
    coaching: "Next time, read the accounts back in the order the caller gave them: \"So that's $114 from your checking to your savings, is that right?\"",
    evidence: { turnIdx: 9, startSeconds: 33.53, quote: "okay and that was from your savings to your checking account" },
  });
  expect(confirm?.subChecks.map((check) => check.result)).toEqual(["failed", "failed"]);
  expect(detail?.typeDetails).toEqual({
    type: "transfer_money",
    fields: [
      { field: "transfer_amount", label: "Amount", callerAsked: "114", logged: "114", result: "match" },
      { field: "transfer_source_account", label: "From", callerAsked: "checking", logged: "savings", result: "reversed" },
      { field: "transfer_destination_account", label: "To", callerAsked: "savings", logged: "checking", result: "reversed" },
    ],
  });
});

test("a 404 means no such call, other failures are passed on", async () => {
  const missing = new CallDetailApi(gatewayAnswering(async () => { throw new ApiError(404, "GET /calls/9 failed (404)"); }));
  expect(await missing.getCallDetail(9)).toBeNull();
  const broken = new CallDetailApi(gatewayAnswering(async () => { throw new ApiError(500, "GET /calls/9 failed (500)"); }));
  await expect(broken.getCallDetail(9)).rejects.toThrow("failed (500)");
});

test("a step or field result the page doesn't know is left off", () => {
  const dto = structuredClone(SAMPLE);
  dto.steps.push({ ...dto.steps[0], key: "invented", status: "praised" });
  dto.steps[4].details.sub_checks.push({ key: "extra", description: "Extra", points: 1, result: "maybe" });
  dto.type_details = {
    type: "transfer_money",
    fields: [
      ...(dto.type_details.fields ?? []),
      { field: "note", label: "Note", caller_asked: "a", logged: "b", result: "unclear" },
    ],
  };
  const detail = new CallDetailApi(gatewayAnswering(async () => dto)).toCallDetail(dto);
  expect(detail.steps.map((step) => step.key)).not.toContain("invented");
  expect(detail.steps.find((step) => step.key === "submit_and_confirm_transfer")?.subChecks).toHaveLength(2);
  expect(detail.typeDetails.fields.map((row) => row.field)).toEqual([
    "transfer_amount", "transfer_source_account", "transfer_destination_account",
  ]);
});

test("a call type without a field table maps to no fields", () => {
  const dto = structuredClone(SAMPLE);
  dto.type_details = { type: "replace_card" };
  expect(new CallDetailApi(gatewayAnswering(async () => dto)).toCallDetail(dto).typeDetails).toEqual({
    type: "replace_card", fields: [],
  });
});

test("a note kind the page doesn't know is left off", () => {
  const dto = structuredClone(SAMPLE);
  dto.transcript[1].notes.push({ kind: "praise", step_key: "greet_and_open", text: "Nice" });
  const turn = new CallDetailApi(gatewayAnswering(async () => dto)).toCallDetail(dto).turns[1];
  expect(turn.notes.map((n) => n.kind)).toEqual(["evidence"]);
});
