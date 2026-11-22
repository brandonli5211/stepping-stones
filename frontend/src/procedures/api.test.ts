import { ProceduresApi, type ProceduresDto } from "./api";

const dto: ProceduresDto = { procedures: [{ call_type: "transfer_money", name: "Transfer money", description: "Move money", steps: [{ key: "confirm", order: 2, step_name: "Confirm", step_description: "Read back" }] }] };

test("reads and maps GET /procedures", async () => {
  const get = vi.fn().mockResolvedValue(dto);
  const procedures = await new ProceduresApi({ get: get as <T>(path: string) => Promise<T> }).getProcedures();
  expect(get).toHaveBeenCalledWith("/procedures");
  expect(procedures).toEqual([{ callType: "transfer_money", name: "Transfer money", description: "Move money", steps: [{ key: "confirm", order: 2, name: "Confirm", description: "Read back" }] }]);
});
