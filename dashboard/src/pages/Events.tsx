import React, { useEffect, useState } from "react";
import { api, Event } from "../api/client";

export default function Events() {
  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getEvents({ limit: 20, offset }).then((res) => {
      setEvents(res.events || []);
      setTotal(res.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [offset]);

  return (
    <div className="page">
      <h2>Events ({total})</h2>
      {loading ? <p>Loading...</p> : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th><th>Type</th><th>Source</th><th>Severity</th><th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.event_id}>
                  <td className="mono">{e.event_id.slice(0, 16)}...</td>
                  <td>{e.event_type}</td>
                  <td>{e.source}</td>
                  <td><span className={`severity ${e.severity}`}>{e.severity}</span></td>
                  <td>{new Date(e.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</button>
            <span>{offset + 1}–{Math.min(offset + 20, total)} of {total}</span>
            <button disabled={offset + 20 >= total} onClick={() => setOffset(offset + 20)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}
