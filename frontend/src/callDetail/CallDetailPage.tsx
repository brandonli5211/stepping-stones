import { useEffect, useSyncExternalStore } from "react";
import { PageHeader, StateMessage } from "../components/pieces";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import type { ViewCallDetailController } from "./controller";
import { FlagList, ScorePanel, Transcript } from "./parts";
import type { CallDetailViewModel } from "./viewModel";

const BACK = { href: "/", label: "Back to my calls" };

// The call detail page (the view). It draws the view model and tells the controller when it opens or a flag
// is chosen. Nothing is computed here.
export default function CallDetailPage({ viewModel, controller }: {
  viewModel: CallDetailViewModel;
  controller: ViewCallDetailController;
}) {
  const state = useSyncExternalStore(viewModel.subscribe, viewModel.getState);
  const selectedStepKey = useSyncExternalStore(viewModel.subscribe, viewModel.selectedStepKey);

  useEffect(() => {
    void controller.load();
  }, [controller]);

  if (state.kind === "loading") {
    return (
      <>
        <PageHeader title="Call review" back={BACK} />
        <p className="text-muted" role="status">{state.message}</p>
      </>
    );
  }

  if (state.kind === "error") {
    return (
      <>
        <PageHeader title="Call review" back={BACK} />
        <Card>
          <CardContent className="flex flex-col items-center">
            <StateMessage kind="error" title={state.title} message={state.message} />
            <button type="button" className="mb-8 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white" onClick={() => void controller.load()}>
              Retry
            </button>
          </CardContent>
        </Card>
      </>
    );
  }

  if (state.kind === "notFound") {
    return (
      <>
        <PageHeader title="Call review" back={{ ...BACK, href: state.backHref }} />
        <Card><CardContent><StateMessage kind="empty" title={state.title} message="This call isn't in your list." /></CardContent></Card>
      </>
    );
  }

  return (
    <>
      <PageHeader title={state.header.title} subtitle={`Call ${state.header.reference}`} back={{ href: state.header.backHref, label: state.header.backLabel }} />
      <div className="flex flex-col gap-6">
        <Card><CardContent className="pt-6"><ScorePanel score={state.score} /></CardContent></Card>
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <Card>
            <CardHeader className="flex flex-row items-baseline justify-between gap-4">
              <CardTitle>Call transcript</CardTitle>
              <span className="text-sm text-muted">{state.transcript.countText}</span>
            </CardHeader>
            <CardContent><Transcript transcript={state.transcript} selectedStepKey={selectedStepKey} /></CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-baseline justify-between gap-4">
              <CardTitle>Flags</CardTitle>
              {state.flags.countText && <span className="text-sm font-semibold text-bad">{state.flags.countText}</span>}
            </CardHeader>
            <CardContent>
              <FlagList flags={state.flags} selectedStepKey={selectedStepKey} onSelect={(key) => controller.selectStep(key)} />
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
