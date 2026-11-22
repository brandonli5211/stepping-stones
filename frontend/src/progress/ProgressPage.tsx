import { useEffect, useState, useSyncExternalStore } from "react";
import { PageHeader, StateMessage, StatusLegend } from "../components/pieces";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import type { ViewProgressController } from "./controller";
import { CallTypeBars, StepRows, WeekChart } from "./parts";
import type { ProgressViewModel } from "./viewModel";

// The Progress page (the view). It draws the view model and tells the controller when it opens. Nothing is computed here.
export default function ProgressPage({ viewModel, controller }: {
  viewModel: ProgressViewModel;
  controller: ViewProgressController;
}) {
  const state = useSyncExternalStore(viewModel.subscribe, viewModel.getState);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    void controller.load();
  }, [controller]);

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <PageHeader title="Your progress" subtitle="How your required steps change week by week." />
        {(state.kind === "ready" || state.kind === "empty") && state.showDemoBadge && <Badge className="mt-3">Demo data</Badge>}
      </div>

      {state.kind === "loading" && <p className="text-muted" role="status">{state.message}</p>}

      {state.kind === "error" && (
        <Card><CardContent><StateMessage kind="error" title={state.title} message={state.message} /></CardContent></Card>
      )}

      {state.kind === "empty" && (
        <Card><CardContent><StateMessage kind="empty" title={state.message} /></CardContent></Card>
      )}

      {state.kind === "ready" && (
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Last 8 weeks</CardTitle>
              <p className="text-xl font-semibold">{state.thisWeekText}</p>
              {state.comparison && <p className="text-muted">{state.comparison}</p>}
            </CardHeader>
            <CardContent><WeekChart weeks={state.weeks} /></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>By call type</CardTitle></CardHeader>
            <CardContent><CallTypeBars callTypes={state.callTypes} /></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Steps you skip most</CardTitle></CardHeader>
            <CardContent className="flex flex-col gap-4">
              <StepRows rows={expanded ? state.allSteps : state.firstSteps} />
              {state.showAllLabel && (
                <button
                  type="button"
                  className="self-start rounded-lg bg-brand-soft px-4 py-2 text-sm font-medium text-brand"
                  aria-expanded={expanded}
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? state.showFewerLabel : state.showAllLabel}
                </button>
              )}
              <StatusLegend />
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
