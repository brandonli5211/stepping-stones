import { useEffect, useRef } from "react";
import { ScoreRing, Stone } from "../components/pieces";
import type { CallDetailReadyState, FlagCardView, TurnLabelView, TurnTone, TurnView } from "./viewModel";

// The drawn pieces of the call detail page. They only draw what the view model gives them.

export function ScorePanel({ score }: { score: CallDetailReadyState["score"] }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-5">
        <ScoreRing value={score.value} band={score.band} suffix="" size={96} />
        <div className="flex min-w-0 flex-col gap-1">
          <p className="text-sm text-muted">{score.value == null ? score.bandLabel : `${score.outOfText} · ${score.bandLabel}`}</p>
          <p className="font-semibold">{score.stepsText}</p>
          {score.lostText && <p className="font-semibold text-bad">{score.lostText}</p>}
          {score.reviewText && <p className="text-sm text-muted">{score.reviewText}</p>}
        </div>
      </div>
      {score.summary && <p className="text-ink">{score.summary}</p>}
    </div>
  );
}

// each tone looks different by more than colour: a border style and the stone on every label
const TONES: Record<TurnTone, string> = {
  plain: "border-transparent",
  evidence: "border-good bg-good/10",
  wrong: "border-bad bg-bad-soft",
};

function TurnLabel({ label }: { label: TurnLabelView }) {
  return (
    <p className={`flex items-center gap-2 text-xs font-semibold ${label.kind === "wrong" ? "text-bad" : "text-ink"}`} data-label={label.kind}>
      <Stone status={label.kind === "wrong" ? "wrong" : "completed"} size={18} label={label.kind === "wrong" ? "Wrong" : "Evidence"} />
      <span>{label.text}</span>
    </p>
  );
}

export function Transcript({ transcript, selectedStepKey }: {
  transcript: CallDetailReadyState["transcript"];
  selectedStepKey: string | null;
}) {
  const turnRefs = useRef(new Map<number, HTMLLIElement>());

  // a chosen step brings its first turn into view
  useEffect(() => {
    if (selectedStepKey == null) return;
    const first = transcript.turns.find((turn) => turn.stepKeys.includes(selectedStepKey));
    if (first) turnRefs.current.get(first.idx)?.scrollIntoView?.({ behavior: "smooth", block: "center" });
  }, [selectedStepKey, transcript]);

  if (transcript.empty) return <p className="py-6 text-muted">Transcript not available</p>;

  return (
    <ol className="flex max-h-[36rem] flex-col gap-2 overflow-y-auto pr-2" aria-label="Call transcript">
      {transcript.turns.map((turn: TurnView) => {
        const selected = selectedStepKey != null && turn.stepKeys.includes(selectedStepKey);
        return (
          <li
            key={turn.idx}
            ref={(el) => { if (el) turnRefs.current.set(turn.idx, el); else turnRefs.current.delete(turn.idx); }}
            className={`flex flex-col gap-1 rounded-lg border-l-4 px-4 py-3 ${TONES[turn.tone]} ${selected ? "ring-2 ring-brand" : ""}`}
            data-tone={turn.tone}
            data-selected={selected}
          >
            <p className="flex gap-3 text-xs text-muted">
              <span className="font-semibold text-ink">{turn.speakerLabel}</span>
              {turn.timeText && <span>{turn.timeText}</span>}
            </p>
            <p className="break-words">{turn.text}</p>
            {turn.labels.map((label, i) => <TurnLabel key={i} label={label} />)}
          </li>
        );
      })}
    </ol>
  );
}

export function FlagList({ flags, selectedStepKey, onSelect }: {
  flags: CallDetailReadyState["flags"];
  selectedStepKey: string | null;
  onSelect: (stepKey: string) => void;
}) {
  if (flags.empty) return <p className="py-2 text-muted">Nothing to fix on this call</p>;
  return (
    <ul className="flex flex-col gap-3">
      {flags.cards.map((card: FlagCardView) => (
        <li key={card.stepKey}>
          <button
            type="button"
            className={`flex w-full flex-col gap-1 rounded-lg border border-bad/40 bg-bad-soft px-4 py-3 text-left ${selectedStepKey === card.stepKey ? "ring-2 ring-brand" : ""}`}
            aria-pressed={selectedStepKey === card.stepKey}
            data-severity={card.severity}
            onClick={() => onSelect(card.stepKey)}
          >
            <span className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-2 font-semibold">
                <Stone status="wrong" size={20} label={card.severity} />
                {card.title}
              </span>
              <span className="shrink-0 font-semibold text-bad">{card.pointsText}</span>
            </span>
            {card.message && <span className="text-sm text-ink">{card.message}</span>}
          </button>
        </li>
      ))}
    </ul>
  );
}
