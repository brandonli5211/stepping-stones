import { createApiGateway } from "./gateway";

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
