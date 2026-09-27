import React, { useEffect, useState } from "react";
import { api, PipelineStatus } from "../api/client";

export default function Overview() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPipelineStatus().then(setStatus).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="page"><h2>Overview</h2><p className="error">Error: {error}</p></div>;
  if (!status) return <div className="page"><h2>Overview</h2><p>Loading...</p></div>;

  return (
    <div className="page">
      <h2>System Overview</h2>
      <div className="status-grid">
        <div className="status-card">
          <h3>Event Backend</h3>
          <p className={`status-badge ${status.event_backend.healthy ? "healthy" : "unhealthy"}`}>
            {status.event_backend.type} — {status.event_backend.healthy ? "Healthy" : "Unhealthy"}
          </p>
        </div>
        <div className="status-card">
          <h3>Search Backend</h3>
          <p className={`status-badge ${status.search_backend.healthy ? "healthy" : "unhealthy"}`}>
            {status.search_backend.type} — {status.search_backend.healthy ? "Healthy" : "Unhealthy"}
          </p>
        </div>
        <div className="status-card">
          <h3>Pipeline Status</h3>
          <p className="status-badge healthy">{status.status}</p>
        </div>
      </div>

      <h3>Pipeline Metrics</h3>
      <table className="metrics-table">
        <thead>
          <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
          {Object.entries(status.metrics).map(([key, value]) => (
            <tr key={key}><td>{key}</td><td>{value}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
