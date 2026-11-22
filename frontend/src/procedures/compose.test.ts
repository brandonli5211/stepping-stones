import { createProceduresScreen, parseProcedureType } from "./compose";

test("accepts a procedure task from the address", () => {
  expect(parseProcedureType("?task=transfer_money")).toBe("transfer_money");
  expect(parseProcedureType("?task=not valid")).toBeNull();
  expect(parseProcedureType("")).toBeNull();
});

test("the composed screen loads procedures through its gateway", async () => {
  const get = vi.fn().mockResolvedValue({ procedures: [] });
  const { viewModel, controller } = createProceduresScreen({ get: get as never });
  await controller.load(null);
  expect(get).toHaveBeenCalledWith("/procedures");
  expect(viewModel.getState()).toEqual({ kind: "empty", message: "No procedures are available yet" });
});
