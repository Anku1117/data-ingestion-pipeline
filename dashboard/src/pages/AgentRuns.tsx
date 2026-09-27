import React, { useEffect, useState } from "react";
import { api, AgentRun } from "../api/client";

export default function AgentRuns() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getRuns({ limit: 20, offset }).then((res) => {
      setRuns(res.runs || []);
      setTotal(res.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [offset]);

  return (
    <div className="page">
      <h2>Agent Runs ({total})</h2>
      {loading ? <p>Loading...</p> : runs.length === 0 ? <p>No agent runs recorded.</p> : (
        <table className="data-table">
          <thead>
            <tr><th>Run ID</th><th>Agent</th><th>Status</th><th>Steps</th><th>Tokens</th><th>Started</th></tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.run_id}>
                <td className="mono">{r.run_id.slice(0, 16)}...</td>
                <td>{r.agent_id}</td>
                <td><span className={`status-badge ${r.status}`}>{r.status}</span></td>
                <td>{r.total_steps}</td>
                <td>{r.total_tokens}</td>
                <td>{new Date(r.started_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
