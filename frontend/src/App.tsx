import { useEffect, useMemo, useState, type MouseEvent } from "react";
import { resolveShellView } from "./application";
import { createApiGateway } from "./gateway";
import { Card, CardContent } from "./components/ui/card";
import CallDetailPage from "./callDetail/CallDetailPage";
import { createCallDetailScreen, parseCallId } from "./callDetail/compose";
import { PageHeader, StateMessage, StatusLegend, Stone, StoneSprite } from "./components/pieces";
import CallsPage from "./CallsPage.jsx";
import { createProgressScreen, parseAgentId } from "./progress/compose";
import ProgressPage from "./progress/ProgressPage";

// all the env stuff gets read here and nowhere else
const api = createApiGateway({
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  sampleData: import.meta.env.VITE_SAMPLE_DATA === "true",
});
const agentSettings = { name: import.meta.env.VITE_AGENT_NAME, role: import.meta.env.VITE_AGENT_ROLE };
// the progress screen's parts, built once: the page draws the view model and calls the controller
const progress = createProgressScreen(api, parseAgentId(import.meta.env.VITE_AGENT_ID));

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  const view = resolveShellView(path, agentSettings);
  // one call detail screen per call id in the address
  const callDetail = useMemo(() => createCallDetailScreen(api, parseCallId(view.callId)), [view.callId]);

  // back/forward buttons
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // grab clicks on our own links so the page doesn't do a full reload
  const onClick = (e: MouseEvent) => {
    const link = (e.target as HTMLElement).closest("a");
    if (!link || link.origin !== window.location.origin || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    window.history.pushState(null, "", link.pathname);
    setPath(link.pathname);
  };

  return (
    <div className="flex min-h-screen text-ink" onClick={onClick}>
      <StoneSprite />
      <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col gap-10 bg-brand px-4 py-10 text-white">
        <div className="flex flex-col gap-3 px-3 text-3xl leading-tight font-semibold">
          <svg viewBox="0 0 32 40" width="32" height="40" className="fill-white" aria-hidden="true">
            <use href="#stone" x="14" y="0" width="16" height="10.4" />
            <use href="#stone" x="4" y="11" width="20" height="13" />
            <use href="#stone" x="0" y="24" width="24" height="15.6" />
          </svg>
          <span>Stepping<br />Stones</span>
        </div>
        <nav className="flex flex-col gap-1">
          {view.menu.map((item) => (
            <a
              key={item.nav}
              href={item.path}
              aria-current={item.current ? "page" : undefined}
              className={`rounded-lg p-3 text-sm ${item.current ? "bg-white/20 font-medium" : "text-white/80 hover:bg-white/10"}`}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="mt-auto flex flex-col px-3 text-sm">
          <strong>{view.agent.name}</strong>
          {view.agent.role && <span className="text-xs text-white/80">{view.agent.role}</span>}
        </div>
      </aside>

      <main className="min-w-0 flex-1 bg-page px-14 py-12">
        {view.screen.id === "my-calls" && <CallsPage />}

        {view.screen.id === "call-detail" && (
          <CallDetailPage key={view.callId} viewModel={callDetail.viewModel} controller={callDetail.controller} />
        )}

        {view.screen.id === "progress" && <ProgressPage viewModel={progress.viewModel} controller={progress.controller} />}

        {view.screen.id === "procedures" && (
          <>
            <PageHeader title={view.screen.title} subtitle="The required steps for each call type." />
            <Card>
              <CardContent className="flex flex-col items-center">
                <Stone status="procedure" size={52} showLabel />
                <StateMessage kind="empty" title="Procedures coming soon" message="Each call type's steps will be listed here." />
              </CardContent>
            </Card>
            <div className="mt-6"><StatusLegend /></div>
          </>
        )}
      </main>
    </div>
  );
}
