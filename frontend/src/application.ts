import { MENU, SCREENS, type AgentProfile, type MenuItem, type Screen } from "./domain";

// the port screens use to get data. gateway.ts is the thing that actually does it
export type ApiGateway = { get<T>(path: string): Promise<T> };

export type ShellView = {
  screen: Screen;
  callId: string | null;
  menu: (MenuItem & { current: boolean })[];
  agent: AgentProfile;
};

// the one use case: address + agent in, what the shell should show out
export function resolveShellView(path: string, agent: { name?: string; role?: string }): ShellView {
  const callId = path.startsWith("/calls/") ? path.slice("/calls/".length) || null : null;
  // anything we don't know just goes to my calls
  const screen = callId ? SCREENS[1] : SCREENS.find((s) => s.path === path) ?? SCREENS[0];
  return {
    screen,
    callId,
    menu: MENU.map((item) => ({ ...item, current: item.nav === screen.nav })),
    agent: { name: agent.name || "Agent", role: agent.role || null },
  };
}
