import { resolveShellView } from "./application";

test("each address opens its screen and marks the right menu item", () => {
  const cases: [string, string, string][] = [
    ["/", "my-calls", "my-calls"],
    ["/calls/7", "call-detail", "my-calls"],
    ["/progress", "progress", "progress"],
    ["/procedures", "procedures", "procedures"],
  ];
  for (const [path, screen, nav] of cases) {
    const view = resolveShellView(path, {});
    expect(view.screen.id).toBe(screen);
    expect(view.menu.filter((m) => m.current).map((m) => m.nav)).toEqual([nav]);
  }
});

test("call detail picks up the call id", () => {
  expect(resolveShellView("/calls/7", {}).callId).toBe("7");
  expect(resolveShellView("/progress", {}).callId).toBeNull();
});

test("unknown addresses fall back to my calls", () => {
  expect(resolveShellView("/nowhere", {}).screen.id).toBe("my-calls");
  expect(resolveShellView("/calls/", {}).screen.id).toBe("my-calls");
});

test("agent shows as configured, or 'Agent' with no role when unset", () => {
  expect(resolveShellView("/", { name: "Robert", role: "Agent" }).agent).toEqual({ name: "Robert", role: "Agent" });
  expect(resolveShellView("/", { name: "", role: "" }).agent).toEqual({ name: "Agent", role: null });
});
