import React, { useEffect, useState } from "react";
import { api, PipelineStatus } from "../api/client";

export default function PipelineHealth() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getPipelineStatus(), api.getPipelineStats()])
      .then(([s, st]) => { setStatus(s); setStats(st); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><h2>Pipeline Health</h2><p>Loading...</p></div>;

  return (
    <div className="page">
      <h2>Pipeline Health</h2>
      {status && (
        <div className="status-grid">
          <div className="status-card">
            <h3>Overall</h3>
            <p className={`status-badge ${status.status === "operational" ? "healthy" : "unhealthy"}`}>
              {status.status}
            </p>
          </div>
          <div className="status-card">
            <h3>Event Backend</h3>
            <p>{status.event_backend.type}</p>
            <p className={`status-badge ${status.event_backend.healthy ? "healthy" : "unhealthy"}`}>
              {status.event_backend.healthy ? "Connected" : "Disconnected"}
            </p>
          </div>
          <div className="status-card">
            <h3>Search Backend</h3>
            <p>{status.search_backend.type}</p>
            <p className={`status-badge ${status.search_backend.healthy ? "healthy" : "unhealthy"}`}>
              {status.search_backend.healthy ? "Connected" : "Disconnected"}
            </p>
          </div>
        </div>
      )}
      {stats && (
        <>
          <h3>Pipeline Statistics</h3>
          <table className="metrics-table">
            <thead><tr><th>Category</th><th>Metric</th><th>Value</th></tr></thead>
            <tbody>
              {Object.entries(stats).map(([category, metrics]) =>
                typeof metrics === "object" && metrics !== null
                  ? Object.entries(metrics).map(([key, value]) => (
                      <tr key={`${category}-${key}`}>
                        <td>{category}</td>
                        <td>{key}</td>
                        <td>{String(value)}</td>
                      </tr>
                    ))
                  : <tr><td>{category}</td><td>-</td><td>{String(metrics)}</td></tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
