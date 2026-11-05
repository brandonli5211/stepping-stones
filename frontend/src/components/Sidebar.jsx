import { useApi } from "../api.js";
import { Link, useRouter } from "../router.jsx";

// Logo: three stones from the shared stone symbol, stacked like a path.
const LOGO_STONES = [
  [14, 0, 16],
  [4, 11, 20],
  [0, 24, 24],
];

/** Left menu: logo, nav (current page highlighted) and the signed-in agent. */
export function Sidebar({ items }) {
  const activeKey = useRouter().match.route.navKey;
  const me = useApi("/api/me");

  return (
    <aside className="sidebar">
      <div className="logo">
        <svg viewBox="0 0 32 40" width="32" height="40" aria-hidden="true">
          {LOGO_STONES.map(([x, y, w]) => (
            <use key={y} href="#stone" x={x} y={y} width={w} height={(w * 26) / 40} />
          ))}
        </svg>
        Stepping
        <br />
        Stones
      </div>
      <nav>
        {items.map((item) => (
          <Link
            key={item.navKey}
            to={item.path}
            className={`sidebar__link ${item.navKey === activeKey ? "is-active" : ""}`}
            aria-current={item.navKey === activeKey ? "page" : undefined}
          >
            {item.navLabel}
          </Link>
        ))}
      </nav>
      <div className="sidebar__user">
        <strong>{me?.name}</strong>
        <span>{me?.role}</span>
      </div>
    </aside>
  );
}
