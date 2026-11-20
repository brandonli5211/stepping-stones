import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";

// no real api in tests. calls page and progress both just get a failed fetch
beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  window.history.pushState(null, "", "/");
});

const marked = () => screen.getByRole("link", { current: "page" }).textContent;
// the calls page shows its own "could not load" alert once its fetch fails
const callsPageSettled = () => screen.findByText(/Could not load calls/);

test("menu click switches screen and marked item", async () => {
  render(<App />);
  await callsPageSettled();
  expect(marked()).toBe("My calls");
  fireEvent.click(screen.getByRole("link", { name: "Procedures" }));
  expect(screen.getByRole("heading", { name: "Procedures" })).toBeTruthy();
  expect(marked()).toBe("Procedures");
});

test("call detail shows the call and keeps my calls marked", () => {
  window.history.pushState(null, "", "/calls/7");
  render(<App />);
  expect(screen.getByRole("heading", { name: "Call 7" })).toBeTruthy();
  expect(marked()).toBe("My calls");
});

test("unknown address shows my calls", async () => {
  window.history.pushState(null, "", "/nowhere");
  render(<App />);
  await callsPageSettled();
  expect(screen.getByRole("heading", { name: "Your calls" })).toBeTruthy();
});

test("progress shows the error message when the api is down", async () => {
  window.history.pushState(null, "", "/progress");
  render(<App />);
  expect((await screen.findByRole("alert")).textContent).toContain("Couldn't load your week");
});

test("agent shows in the menu, 'Agent' when nothing is configured", async () => {
  render(<App />);
  await callsPageSettled();
  expect(screen.getByText("Agent")).toBeTruthy();
});
