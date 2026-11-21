import { ApiError } from "./application";
import { createApiGateway, sampleKey } from "./gateway";

type Calls = { calls: { score: number }[] };

test("sample mode answers /calls without touching fetch", async () => {
  const fetchImpl = vi.fn();
  const api = createApiGateway({ apiUrl: "http://api", sampleData: true, fetchImpl });
  const data = await api.get<Calls>("/calls");
  expect(data.calls[0].score).toBe(75);
  expect(fetchImpl).not.toHaveBeenCalled();
});

test("sample mode rejects paths it has no sample for", async () => {
  const api = createApiGateway({ apiUrl: "http://api", sampleData: true });
  await expect(api.get("/nope")).rejects.toThrow("no sample data for /nope");
});

test("real mode fetches apiUrl + path and returns the json", async () => {
  const fetchImpl = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: 1 }), { status: 200 }));
  const api = createApiGateway({ apiUrl: "http://api", sampleData: false, fetchImpl });
  expect(await api.get("/calls")).toEqual({ ok: 1 });
  expect(fetchImpl).toHaveBeenCalledWith("http://api/calls");
});

test("real mode rejects when the api says no", async () => {
  const fetchImpl = vi.fn().mockResolvedValue(new Response("", { status: 500 }));
  const api = createApiGateway({ apiUrl: "http://api", sampleData: false, fetchImpl });
  await expect(api.get("/calls")).rejects.toThrow("GET /calls failed (500)");
});

test("an error status rejects with an ApiError that carries the status", async () => {
  const fetchImpl = vi.fn().mockResolvedValue(new Response("", { status: 404 }));
  const api = createApiGateway({ apiUrl: "http://api", sampleData: false, fetchImpl });
  const error = await api.get("/calls/9").catch((e: unknown) => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toBeInstanceOf(Error);
  expect((error as ApiError).status).toBe(404);
});

test("sampleKey maps every numeric call path to the call detail sample", () => {
  expect(sampleKey("/calls/1")).toBe("/calls/{id}");
  expect(sampleKey("/calls/42?x=1")).toBe("/calls/{id}");
  expect(sampleKey("/calls")).toBe("/calls");
  expect(sampleKey("/calls/abc")).toBe("/calls/abc");
});

test("sample mode answers any /calls/{n} with the Transfer money call", async () => {
  const api = createApiGateway({ apiUrl: "http://api", sampleData: true });
  type Detail = { header: { call_type_name: string }; score: { score: number }; transcript: unknown[] };
  for (const path of ["/calls/1", "/calls/7"]) {
    const data = await api.get<Detail>(path);
    expect(data.header.call_type_name).toBe("Transfer money");
    expect(data.score.score).toBe(45);
    expect(data.transcript).toHaveLength(16);
  }
});
