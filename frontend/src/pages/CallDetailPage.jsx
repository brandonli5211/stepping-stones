// Page: one call. Later this becomes the post-call summary (steps completed / missed, score).
import { Link, useParams } from 'react-router-dom';

import { getCall } from '../api/client.js';
import useApi from '../hooks/useApi.js';
import Transcript from '../components/Transcript.jsx';

export default function CallDetailPage() {
  const { callId } = useParams();
  const { data: call, error, loading } = useApi(() => getCall(callId), [callId]);

  if (loading) return <p>Loading call…</p>;
  if (error) return <p role="alert">Could not load call {callId}: {error.message}</p>;

  const logged = Object.entries(call.captured_by_agent);

  return (
    <section>
      <p><Link to="/">← All calls</Link></p>
      <h1>{call.id}</h1>
      <p className="meta">
        Agent <strong>{call.agent_id}</strong> · Task <strong>{call.task_type}</strong>
      </p>

      {/* TODO (scoring ticket): step checklist + score goes here */}

      <h2>Logged by agent</h2>
      {logged.length === 0 ? (
        <p>Nothing logged.</p>
      ) : (
        <ul>
          {logged.map(([field, value]) => (
            <li key={field}>{field}: <strong>{String(value)}</strong></li>
          ))}
        </ul>
      )}

      <h2>Transcript</h2>
      <Transcript turns={call.turns} />
    </section>
  );
}
