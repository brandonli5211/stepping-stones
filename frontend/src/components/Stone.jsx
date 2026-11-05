// The stone artwork is drawn once in <StoneSprite> and reused everywhere with <use>.
const VIEWBOX = "0 0 40 26";

export const STATUS_LABELS = {
  completed: "Completed",
  missed: "Missed",
  wrong: "Wrong",
  review: "Under review",
  procedure: "Procedure step",
};

export function StoneSprite() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <symbol id="stone" viewBox={VIEWBOX}>
        <path d="M3.2 12.6C3.6 6.9 10.4 3.2 19.6 3.1c9.6-.1 16.9 3.4 17.3 9 .4 5.9-7.2 9.7-17.6 9.8C9.4 22 2.8 18.4 3.2 12.6Z" />
      </symbol>
      <symbol id="stone-crack" viewBox={VIEWBOX}>
        <path d="M18.5 3.4l2.6 5.2-4.1 3.7 4.6 4.3-2.1 5.2" fill="none" />
      </symbol>
      <symbol id="stone-mark" viewBox={VIEWBOX}>
        <path d="M16.2 8.6l7.6 7.6M23.8 8.6l-7.6 7.6" fill="none" />
      </symbol>
    </svg>
  );
}

const SIZES = { sm: 26, md: 36, lg: 52 };
const DETAIL = { missed: "#stone-crack", wrong: "#stone-mark" };

/** A step stone. Shape, colour and a text label all show the status. */
export function Stone({ status, size = "md", label = STATUS_LABELS[status], showLabel = false }) {
  const width = SIZES[size];
  return (
    <span className={`stone stone--${status}`} title={label}>
      <svg viewBox={VIEWBOX} width={width} height={(width * 26) / 40} aria-hidden="true">
        <use href="#stone" className="stone__edge" y="1.6" />
        <use href="#stone" className="stone__face" />
        {DETAIL[status] && <use href={DETAIL[status]} className="stone__detail" />}
      </svg>
      <span className={showLabel ? "stone__label" : "visually-hidden"}>{label}</span>
    </span>
  );
}

export function StoneRow({ steps }) {
  return (
    <span className="row">
      {steps.map((step, i) => (
        <Stone key={i} status={step.status} size="sm" label={`${step.name}: ${STATUS_LABELS[step.status]}`} />
      ))}
    </span>
  );
}

export function StatusLegend() {
  return (
    <span className="row legend">
      {["completed", "missed", "wrong", "review"].map((s) => (
        <Stone key={s} status={s} size="sm" showLabel />
      ))}
    </span>
  );
}
