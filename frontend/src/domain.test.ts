import { BAND_LABELS, scoreBand } from "./domain";

test("scoreBand puts the edge scores in the right band", () => {
  expect(scoreBand(100)).toBe("on_track");
  expect(scoreBand(85)).toBe("on_track");
  expect(scoreBand(84)).toBe("getting_there");
  expect(scoreBand(60)).toBe("getting_there");
  expect(scoreBand(59)).toBe("focus_here");
  expect(scoreBand(0)).toBe("focus_here");
  expect(scoreBand(null)).toBeNull();
});

test("every band has a label", () => {
  expect(BAND_LABELS).toEqual({ on_track: "On track", getting_there: "Getting there", focus_here: "Focus here" });
});
