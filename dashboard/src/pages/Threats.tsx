import React, { useEffect, useState } from "react";
import { api, ThreatAlert } from "../api/client";

export default function Threats() {
  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{ total_alerts: number; active_rules: number } | null>(null);

  useEffect(() => {
    api.getThreatStats().then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api.getThreats({ limit: 20, offset }).then((res) => {
      setAlerts(res.alerts || []);
      setTotal(res.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [offset]);

  return (
    <div className="page">
      <h2>Threat Detection</h2>
      {stats && (
        <div className="status-grid">
          <div className="status-card"><h3>Total Alerts</h3><p>{stats.total_alerts}</p></div>
          <div className="status-card"><h3>Active Rules</h3><p>{stats.active_rules}</p></div>
        </div>
      )}
      <h3>Alerts ({total})</h3>
      {loading ? <p>Loading...</p> : alerts.length === 0 ? <p>No threats detected.</p> : (
        <table className="data-table">
          <thead>
            <tr><th>Alert ID</th><th>Type</th><th>Severity</th><th>Confidence</th><th>Source</th><th>Description</th></tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.alert_id}>
                <td className="mono">{a.alert_id.slice(0, 16)}...</td>
                <td>{a.threat_type}</td>
                <td><span className={`severity ${a.severity}`}>{a.severity}</span></td>
                <td>{(a.confidence * 100).toFixed(0)}%</td>
                <td>{a.source}</td>
                <td>{a.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
