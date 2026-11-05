import { useApi } from "../api.js";
import { Card, EmptyState } from "../components/Card.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { ScoreRing } from "../components/ScoreRing.jsx";
import { StatusLegend, Stone } from "../components/Stone.jsx";
import { StepList } from "../components/StepList.jsx";
import { paths } from "../router.jsx";

export default function CallDetailPage({ params }) {
  const call = useApi(`/api/calls/${params.callId}`);
  if (!call) return null;

  return (
    <>
      <PageHeader
        back={{ to: paths.myCalls, label: "Back to my calls" }}
        leading={<Stone status="procedure" size="lg" />}
        title={call.callType}
        subtitle={`Call ${call.id} · ${call.date} at ${call.time}`}
      />
      <div className="detail-grid">
        <Card title="Call transcript" meta="Coming soon">
          <EmptyState
            title="Transcript goes here"
            message="Agent and customer turns, with evidence for each step highlighted."
          />
        </Card>
        <div className="stack">
          <Card className="summary">
            <ScoreRing value={call.score} size={72} stroke={8} tone={call.score === 100 ? "good" : "bad"} />
            <p className="summary__headline">
              {call.completed} of {call.total} steps
            </p>
          </Card>
          <Card title="Required steps">
            <StepList steps={call.steps} />
            <StatusLegend />
          </Card>
        </div>
      </div>
    </>
  );
}
