import { useState } from "react";
import type { ExecItem, Meeting } from "../types";
import { ItemRow } from "../components/ItemRow";

export default function MeetingsView({
  meetings,
  items,
  replayToday,
}: {
  meetings: Meeting[];
  items: ExecItem[];
  replayToday: string;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const detail = meetings.find((m) => m.id === selected) ?? null;
  const detailItems = detail ? items.filter((i) => i.meeting === detail.id) : [];

  return (
    <div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Meeting</th>
            <th>Date</th>
            <th>Items</th>
            <th>Avg risk</th>
            <th>Overdue</th>
          </tr>
        </thead>
        <tbody>
          {meetings.map((m) => (
            <tr
              key={m.id}
              className={selected === m.id ? "selected" : "clickable"}
              onClick={() => setSelected(selected === m.id ? null : m.id)}
            >
              <td>
                <strong>{m.id}</strong>
              </td>
              <td>{m.meeting_date}</td>
              <td>{m.items}</td>
              <td>{m.avg_risk.toFixed(1)}</td>
              <td>{m.overdue}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {detail && (
        <div className="panel">
          <div className="panel-head">
            <h3>{detail.id}</h3>
            <button className="link-btn" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          <div className="summary-grid">
            <div className="stat">
              <div className="stat-num">{detail.turns}</div>
              <div className="stat-label">turns</div>
            </div>
            <div className="stat">
              <div className="stat-num">{detail.items}</div>
              <div className="stat-label">items</div>
            </div>
            <div className="stat">
              <div className="stat-num">{detail.ownerless}</div>
              <div className="stat-label">ownerless</div>
            </div>
            <div className="stat">
              <div className="stat-num">{detail.dateless}</div>
              <div className="stat-label">dateless</div>
            </div>
            <div className="stat">
              <div className="stat-num">{detail.overdue}</div>
              <div className="stat-label">overdue</div>
            </div>
            <div className="stat">
              <div className="stat-num">{detail.avg_risk.toFixed(1)}</div>
              <div className="stat-label">avg risk</div>
            </div>
          </div>
          {detail.top_risks.length > 0 && (
            <p className="hint">
              Top risks: {detail.top_risks.join(", ")}
            </p>
          )}
          <h4>Extracted items</h4>
          <div className="item-list">
            {[...detailItems]
              .sort((a, b) => b.risk.score - a.risk.score)
              .map((i) => (
                <ItemRow key={i.id} item={i} replayToday={replayToday} showMeeting={false} />
              ))}
          </div>
          {detailItems.length === 0 && <p className="empty">No items extracted for this meeting.</p>}
        </div>
      )}
    </div>
  );
}
