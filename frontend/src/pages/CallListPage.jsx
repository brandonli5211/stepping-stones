// Page: list of calls. Later this becomes the agent's call history (with scores).
import { Link } from 'react-router-dom';

import { listCalls } from '../api/client.js';
import useApi from '../hooks/useApi.js';

export default function CallListPage() {
  const { data: calls, error, loading } = useApi(listCalls, []);

  if (loading) return <p>Loading calls…</p>;
  if (error) return <p role="alert">Could not load calls: {error.message}. Is the API running?</p>;
  if (calls.length === 0) return <p>No calls yet. Run the seed script (see docs/SETUP.md).</p>;

  return (
    <section>
      <h1>Calls</h1>
      <table className="table">
        <thead>
          <tr>
            <th>Call</th>
            <th>Agent</th>
            <th>Task type</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((call) => (
            <tr key={call.id}>
              <td><Link to={`/calls/${call.id}`}>{call.id}</Link></td>
              <td>{call.agent_id}</td>
              <td>{call.task_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
