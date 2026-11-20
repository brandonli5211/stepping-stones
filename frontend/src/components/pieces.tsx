import { STATUS_LABELS, type StepStatus } from "../domain";

// the reusable bits every screen shares. they only draw what they're given, no deciding

const VIEWBOX = "0 0 40 26";

// the stone art lives here once, every stone (and the logo) just <use>s it
export function StoneSprite() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden="true">
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

// each status gets its own look so color isn't the only clue
const LOOKS: Record<StepStatus, { face: string; detail?: string }> = {
  completed: { face: "fill-good" },
  missed: { face: "fill-bad-soft stroke-bad", detail: "#stone-crack" },
  wrong: { face: "fill-bad", detail: "#stone-mark" },
  under_review: { face: "fill-transparent stroke-review [stroke-dasharray:2.4_2]" },
  procedure: { face: "fill-brand" },
};

export function Stone({ status, label, size = 26, showLabel = false }: {
  status: string;
  label?: string;
  size?: number;
  showLabel?: boolean;
}) {
  // anything we don't recognise is shown as under review
  const known = (status in LOOKS ? status : "under_review") as StepStatus;
  const look = LOOKS[known];
  const text = label ?? STATUS_LABELS[known];
  return (
    <span className="inline-flex items-center gap-2" title={text} data-status={known}>
      <svg viewBox={VIEWBOX} width={size} height={(size * 26) / 40} className="overflow-visible" aria-hidden="true">
        <use href="#stone" className={`${look.face} stroke-[1.2]`} />
        {look.detail && (
          <use href={look.detail} className={known === "wrong" ? "stroke-white stroke-2" : "stroke-bad stroke-[1.4]"} />
        )}
      </svg>
      <span className={showLabel ? "text-xs text-muted" : "sr-only"}>{text}</span>
    </span>
  );
}

export function StatusLegend() {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Stone key">
      {(["completed", "missed", "wrong", "under_review"] as const).map((s) => (
        <Stone key={s} status={s} size={20} showLabel />
      ))}
    </div>
  );
}

// just shows the score it gets. "–" when there isn't one yet
export function ScoreRing({ value, size = 88 }: { value: number | null; size?: number }) {
  const r = size / 2 - 5;
  const length = 2 * Math.PI * r;
  return (
    <div className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }} role="img" aria-label={value == null ? "No score yet" : `Score ${value}%`}>
      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} strokeWidth="9" className="fill-none stroke-brand-soft" />
        <circle
          cx={size / 2} cy={size / 2} r={r} strokeWidth="9" strokeLinecap="round"
          strokeDasharray={length} strokeDashoffset={length * (1 - (value ?? 0) / 100)}
          className="fill-none stroke-brand"
        />
      </svg>
      <span className="font-bold" style={{ fontSize: size * 0.22 }}>{value == null ? "–" : `${value}%`}</span>
    </div>
  );
}

export function PageHeader({ title, subtitle, back }: {
  title: string;
  subtitle?: string;
  back?: { href: string; label: string };
}) {
  return (
    <header className="mb-6 flex flex-col items-start gap-2">
      {back && (
        <a href={back.href} className="mb-3 rounded-full border border-black/10 bg-white px-3 py-1 text-xs">
          ← {back.label}
        </a>
      )}
      <h1 className="text-4xl font-semibold tracking-tight">{title}</h1>
      {subtitle && <p className="text-muted">{subtitle}</p>}
    </header>
  );
}

// one thing for both "nothing here" and "that broke"
export function StateMessage({ kind, title, message }: { kind: "empty" | "error"; title: string; message?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-12 text-center" role={kind === "error" ? "alert" : undefined}>
      <Stone status={kind === "error" ? "missed" : "under_review"} size={52} label={title} />
      <h2 className="text-lg font-semibold">{title}</h2>
      {message && <p className="max-w-md text-muted">{message}</p>}
    </div>
  );
}
