import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Trajectory() {
  const [runId, setRunId] = useState("");
  const [trajectory, setTrajectory] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  const loadTrajectory = async () => {
    if (!runId.trim()) return;
    try {
      const data = await api.getTrajectory(runId.trim());
      setTrajectory(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
      setTrajectory(null);
    }
  };

  return (
    <div className="page">
      <h2>Agent Trajectory</h2>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Enter run_id (e.g., run_abc123...)"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadTrajectory()}
        />
        <button onClick={loadTrajectory}>Load</button>
      </div>
      {error && <p className="error">Error: {error}</p>}
      {trajectory && (
        <div className="trajectory-view">
          <h3>Trajectory for {runId}</h3>
          <pre>{JSON.stringify(trajectory, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
