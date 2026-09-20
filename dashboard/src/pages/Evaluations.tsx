import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Evaluations() {
  const [evaluations, setEvaluations] = useState<unknown[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getEvaluations({ limit: 20, offset }).then((res) => {
      setEvaluations(res.evaluations || []);
      setTotal(res.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [offset]);

  return (
    <div className="page">
      <h2>Evaluations ({total})</h2>
      {loading ? <p>Loading...</p> : evaluations.length === 0 ? <p>No evaluations recorded.</p> : (
        <table className="data-table">
          <thead>
            <tr><th>Run ID</th><th>Agent</th><th>Score</th><th>Success</th><th>Tokens</th></tr>
          </thead>
          <tbody>
            {evaluations.map((ev: any, i) => (
              <tr key={i}>
                <td className="mono">{ev.run_id?.slice(0, 16)}...</td>
                <td>{ev.agent_id}</td>
                <td>{(ev.score * 100).toFixed(0)}%</td>
                <td><span className={`status-badge ${ev.success ? "completed" : "failed"}`}>{ev.success ? "Yes" : "No"}</span></td>
                <td>{ev.total_tokens}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
