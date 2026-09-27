import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function DLQ() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getEvents({ event_type: "DLQ", limit: 50 })
      .then((res) => { setEvents(res.events || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <h2>Dead Letter Queue</h2>
      <p className="info">Events that failed validation or processing appear here.</p>
      {loading ? <p>Loading...</p> : events.length === 0 ? (
        <div className="empty-state">
          <h3>DLQ is empty</h3>
          <p>No events have been routed to the Dead Letter Queue.</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr><th>Event ID</th><th>Type</th><th>Source</th><th>Timestamp</th></tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.event_id}>
                <td className="mono">{e.event_id?.slice(0, 16)}...</td>
                <td>{e.event_type}</td>
                <td>{e.source}</td>
                <td>{new Date(e.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
