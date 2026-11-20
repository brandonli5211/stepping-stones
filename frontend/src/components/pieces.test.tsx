import { render, screen } from "@testing-library/react";
import { cn } from "../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { PageHeader, ScoreRing, StateMessage, StatusLegend, Stone, StoneSprite } from "./pieces";

test("cn joins classes and lets the later tailwind class win", () => {
  expect(cn("px-2", false && "hidden", "px-4")).toBe("px-4");
});

test("card parts render their content", () => {
  render(<Card><CardHeader><CardTitle>Title</CardTitle></CardHeader><CardContent>Body</CardContent></Card>);
  expect(screen.getByText("Title")).toBeTruthy();
  expect(screen.getByText("Body")).toBeTruthy();
});

test("sprite defines the shared stone symbols", () => {
  const { container } = render(<StoneSprite />);
  expect(container.querySelectorAll("symbol")).toHaveLength(3);
});

test("every stone has a text label, unknown ones show as under review", () => {
  render(<><Stone status="missed" /><Stone status="wrong" /><Stone status="banana" /></>);
  expect(screen.getByText("Missed")).toBeTruthy();
  expect(screen.getByText("Wrong")).toBeTruthy();
  expect(screen.getByText("Under review")).toBeTruthy();
});

test("legend lists the four call statuses", () => {
  render(<StatusLegend />);
  for (const label of ["Completed", "Missed", "Wrong", "Under review"]) expect(screen.getByText(label)).toBeTruthy();
});

test("score ring shows exactly what it's given", () => {
  render(<><ScoreRing value={75} /><ScoreRing value={null} /></>);
  expect(screen.getByRole("img", { name: "Score 75%" }).textContent).toBe("75%");
  expect(screen.getByRole("img", { name: "No score yet" }).textContent).toBe("–");
});

test("page header shows title, subtitle and back link", () => {
  render(<PageHeader title="Call 7" subtitle="Soon" back={{ href: "/", label: "Back to my calls" }} />);
  expect(screen.getByRole("heading", { name: "Call 7" })).toBeTruthy();
  expect(screen.getByText("Soon")).toBeTruthy();
  expect(screen.getByRole("link").getAttribute("href")).toBe("/");
});

test("state message: error is an alert, empty isn't", () => {
  render(<><StateMessage kind="error" title="Broke" /><StateMessage kind="empty" title="Nothing" /></>);
  expect(screen.getByRole("alert").textContent).toContain("Broke");
  expect(screen.getAllByRole("alert")).toHaveLength(1);
});
