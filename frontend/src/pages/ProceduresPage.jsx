import { useApi } from "../api.js";
import { Card } from "../components/Card.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { StepList } from "../components/StepList.jsx";

export default function ProceduresPage() {
  const procedures = useApi("/api/procedures");
  if (!procedures) return null;

  return (
    <>
      <PageHeader title="Procedures" subtitle="The required steps for each call type." />
      <div className="card-grid">
        {procedures.map((p) => (
          <Card key={p.id} title={p.callType} meta={`${p.steps.length} steps`}>
            <StepList steps={p.steps.map((name) => ({ name, status: "procedure" }))} numbered />
          </Card>
        ))}
      </div>
    </>
  );
}
