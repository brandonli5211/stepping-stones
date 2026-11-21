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
});

test("a 404 means no such call, other failures are passed on", async () => {
  const missing = new CallDetailApi(gatewayAnswering(async () => { throw new ApiError(404, "GET /calls/9 failed (404)"); }));
  expect(await missing.getCallDetail(9)).toBeNull();
  const broken = new CallDetailApi(gatewayAnswering(async () => { throw new ApiError(500, "GET /calls/9 failed (500)"); }));
  await expect(broken.getCallDetail(9)).rejects.toThrow("failed (500)");
});

test("a note kind the page doesn't know is left off", () => {
  const dto = structuredClone(SAMPLE);
  dto.transcript[1].notes.push({ kind: "praise", step_key: "greet_and_open", text: "Nice" });
  const turn = new CallDetailApi(gatewayAnswering(async () => dto)).toCallDetail(dto).turns[1];
  expect(turn.notes.map((n) => n.kind)).toEqual(["evidence"]);
});
