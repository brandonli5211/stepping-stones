import { useEffect, useSyncExternalStore } from "react";
import { PageHeader, StateMessage, Stone, StoneLoader } from "../components/pieces";
import { Card, CardContent } from "../components/ui/card";
import type { ViewProceduresController } from "./controller";
import type { ProceduresViewModel } from "./viewModel";

export default function ProceduresPage({ viewModel, controller, selectedCallType }: { viewModel: ProceduresViewModel; controller: ViewProceduresController; selectedCallType: string | null }) {
  const state = useSyncExternalStore(viewModel.subscribe, viewModel.getState);
  useEffect(() => { void controller.load(selectedCallType); }, [controller, selectedCallType]);
  const select = (callType: string) => {
    if (!controller.selectProcedure(callType)) return;
    window.history.replaceState(null, "", `/procedures?task=${encodeURIComponent(callType)}`);
  };
  return (
    <>
      <PageHeader title="Procedures" subtitle="The required steps for each call type." />
      {state.kind === "loading" && <StoneLoader message={state.message} />}
      {state.kind === "error" && <Card><CardContent><StateMessage kind="error" title={state.title} message={state.message} /></CardContent></Card>}
      {state.kind === "empty" && <Card><CardContent><StateMessage kind="empty" title={state.message} /></CardContent></Card>}
      {state.kind === "ready" && <div className="flex max-w-4xl flex-col gap-6">
        <div className="flex flex-wrap gap-2" aria-label="Procedure type">
          {state.procedures.map((tab) => <button key={tab.callType} type="button" aria-pressed={tab.callType === state.selectedCallType} onClick={() => select(tab.callType)} className={`rounded-lg px-4 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${tab.callType === state.selectedCallType ? "bg-brand text-white" : "bg-white text-ink shadow-sm hover:bg-brand-soft"}`}>{tab.name}</button>)}
        </div>
        <Card><CardContent className="pt-6"><p className="text-sm font-medium text-brand">Procedure</p><h2 className="mt-1 text-2xl font-semibold">{state.name}</h2><p className="mt-2 max-w-2xl text-muted">{state.description}</p></CardContent></Card>
        <ol className="relative ml-4 flex flex-col gap-4 border-l-2 border-brand-soft pl-8" aria-label={`${state.name} steps`}>
          {state.steps.map((step) => <li key={step.key} className="relative"><span className="absolute -left-[49px] top-5 grid h-8 w-8 place-items-center rounded-full bg-page"><Stone status="procedure" size={28} /></span><Card><CardContent className="py-5"><p className="text-xs font-semibold tracking-wide text-brand">STEP {step.order}</p><h3 className="mt-1 font-semibold">{step.name}</h3>{step.description && <p className="mt-1 text-sm text-muted">{step.description}</p>}</CardContent></Card></li>)}
        </ol>
      </div>}
    </>
  );
}
