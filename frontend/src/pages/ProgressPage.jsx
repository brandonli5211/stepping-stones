import { useApi } from "../api.js";
import { Card, EmptyState } from "../components/Card.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { SummaryCard } from "../components/ScoreRing.jsx";

export default function ProgressPage() {
  const data = useApi("/api/progress");
  if (!data) return null;

  return (
    <>
      <PageHeader title="Your progress" subtitle="How your required steps have changed week by week." />
      <div className="stack">
        <SummaryCard summary={data.summary} />
        <Card>
          <EmptyState
            title="Weekly chart and habits go here"
            message="Score by week, and which steps you complete every time or keep missing."
          />
        </Card>
      </div>
    </>
  );
}
