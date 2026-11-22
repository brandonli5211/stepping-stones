import { SAMPLE_CALL_DETAIL } from "../sampleCallDetail";
import { createCallDetailScreen, parseCallId } from "./compose";

test("parseCallId takes a whole number of 1 or more", () => {
  expect(parseCallId("1")).toBe(1);
  expect(parseCallId("42")).toBe(42);
  for (const bad of ["0", "abc", "1.5", "-3", "", "07", "1/2", null, undefined]) expect(parseCallId(bad)).toBeNull();
});

test("the screen loads the call through the gateway", async () => {
  const get = vi.fn().mockResolvedValue(SAMPLE_CALL_DETAIL);
  const { viewModel, controller } = createCallDetailScreen({ get: get as never }, 1);
  await controller.load();
  expect(get).toHaveBeenCalledWith("/calls/1");
  expect(viewModel.getState().kind).toBe("ready");
});

test("no call id: not found, and no request", async () => {
  const get = vi.fn();
  const { viewModel, controller } = createCallDetailScreen({ get: get as never }, null);
  await controller.load();
  expect(get).not.toHaveBeenCalled();
  expect(viewModel.getState().kind).toBe("notFound");
});
