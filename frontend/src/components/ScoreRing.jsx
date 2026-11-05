import { Card } from "./Card.jsx";

/** Circular score with the percentage in the middle. tone: "brand" | "good" | "bad". */
export function ScoreRing({ value, size = 88, stroke = 9, tone = "brand" }) {
  const r = (size - stroke) / 2;
  const c = size / 2;
  const length = 2 * Math.PI * r;
  return (
    <div className={`ring ring--${tone}`} style={{ width: size, height: size }} role="img" aria-label={`Score ${value}%`}>
      <svg width={size} height={size}>
        <circle className="ring__track" cx={c} cy={c} r={r} strokeWidth={stroke} />
        <circle
          className="ring__arc"
          cx={c}
          cy={c}
          r={r}
          strokeWidth={stroke}
          strokeDasharray={length}
          strokeDashoffset={length * (1 - value / 100)}
          transform={`rotate(-90 ${c} ${c})`}
        />
      </svg>
      <span style={{ fontSize: size * 0.22 }}>{value}%</span>
    </div>
  );
}

/** Score ring + "This week · 35 of 39 required steps completed" + optional action. */
export function SummaryCard({ summary, action }) {
  return (
    <Card className="summary">
      <ScoreRing value={summary.score} />
      <div>
        <span className="muted small">This week</span>
        <p className="summary__headline">
          {summary.completed} of {summary.total} required steps completed
        </p>
        <span className="muted small">{summary.change}</span>
      </div>
      {action}
    </Card>
  );
}
