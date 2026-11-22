import { act, fireEvent, render, screen } from "@testing-library/react";
import { SAMPLE_CALL_DETAIL } from "../sampleCallDetail";
import { CallDetailApi, type CallDetailDto } from "./api";
import CallDetailPage from "./CallDetailPage";
import { ViewCallDetailController } from "./controller";
import { ViewCallDetailOutputData } from "./outputData";
import { ViewCallDetailPresenter } from "./presenter";
import { CallDetailViewModel } from "./viewModel";

function setUp() {
  const viewModel = new CallDetailViewModel();
  const execute = vi.fn().mockResolvedValue(undefined);
  const controller = new ViewCallDetailController({ execute }, 1, viewModel);
  render(<CallDetailPage viewModel={viewModel} controller={controller} />);
  return { viewModel, execute, presenter: new ViewCallDetailPresenter(viewModel) };
}

const sample = () => new ViewCallDetailOutputData(
  new CallDetailApi({ get: async () => { throw new Error("unused"); } }).toCallDetail(SAMPLE_CALL_DETAIL as unknown as CallDetailDto),
);

test("loads the call when it opens and shows loading", () => {
  const { execute } = setUp();
  expect(execute).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("status").textContent).toContain("Loading this call");
});

test("error state retries", () => {
  const { execute, presenter } = setUp();
  act(() => presenter.prepareFailView("GET /calls/1 failed (503)"));
  expect(screen.getByRole("alert").textContent).toContain("Couldn't load this call");
  fireEvent.click(screen.getByRole("button", { name: "Retry" }));
  expect(execute).toHaveBeenCalledTimes(2);
});

test("not found state links back to my calls", () => {
  const { presenter } = setUp();
  act(() => presenter.prepareNotFoundView());
  expect(screen.getByRole("heading", { name: "Call not found" })).toBeTruthy();
  expect(screen.getByRole("link", { name: /Back to my calls/ }).getAttribute("href")).toBe("/");
});

test("ready: the Transfer money call, and choosing the flag highlights the 0:33 and 0:44 turns", () => {
  Element.prototype.scrollIntoView = vi.fn();
  const { presenter } = setUp();
  act(() => presenter.prepareSuccessView(sample()));
  expect(screen.getByRole("heading", { name: "Transfer money" })).toBeTruthy();
  expect(screen.getByText("Call a2f086d27b3a4f96")).toBeTruthy();
  expect(screen.getByText("9 turns, verbatim")).toBeTruthy();
  expect(screen.getByText("1 critical, 55 points lost")).toBeTruthy();
  const turns = () => screen.getAllByRole("listitem").filter((li) => li.dataset.tone);
  expect(turns()).toHaveLength(9);
  expect(turns().filter((t) => t.dataset.selected === "true")).toHaveLength(0);

  fireEvent.click(screen.getByRole("button", { name: /Submit and confirm transfer/ }));
  const highlighted = turns().filter((t) => t.dataset.selected === "true");
  expect(highlighted.map((t) => t.textContent?.match(/\d:\d\d/)?.[0])).toEqual(["0:33", "0:44"]);
});
