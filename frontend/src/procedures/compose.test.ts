import { parseProcedureType } from "./compose";

test("accepts a procedure task from the address", () => {
  expect(parseProcedureType("?task=transfer_money")).toBe("transfer_money");
  expect(parseProcedureType("?task=not valid")).toBeNull();
  expect(parseProcedureType("")).toBeNull();
});
