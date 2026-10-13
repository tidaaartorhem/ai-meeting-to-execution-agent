import { useState } from "react";
import type { ExecItem, Tier } from "../types";
import { isOverdue } from "../types";

export function TierChip({ tier }: { tier: Tier }) {
  const cls = tier.replace(" ", "-");
  return <span className={`chip tier-${cls}`}>{tier}</span>;
}

export function ItemRow({
  item,
  replayToday,
  showMeeting = true,
  defaultOpen = false,
}: {
  item: ExecItem;
  replayToday: string;
  showMeeting?: boolean;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const overdue = isOverdue(item, replayToday);

  return (
    <div className="item-row">
      <div className="item-main">
        <div className="item-top">
          <TierChip tier={item.risk.tier} />
          {overdue && <span className="chip overdue">OVERDUE</span>}
          <span className="item-text">{item.text}</span>
        </div>
        <div className="item-meta">
          <span>
            <strong>Owner:</strong> {item.owner}
          </span>
          <span>
            <strong>Due:</strong> {item.due ? item.due.date : "no date"}
          </span>
          {showMeeting && (
            <span>
              <strong>Meeting:</strong> {item.meeting}
            </span>
          )}
          <span className="rule-tag">
            {item.rule} · {Math.round(item.confidence * 100)}%
          </span>
        </div>
        <button className="link-btn" onClick={() => setOpen(!open)}>
          {open ? "Hide evidence" : "Show evidence"}
        </button>
        {open && (
          <div className="evidence">
            <div className="evidence-quote">“{item.quote}”</div>
            <div className="evidence-meta">
              <span>Speaker: {item.speaker}</span>
              <span>Rule fired: {item.rule}</span>
              <span>Confidence: {Math.round(item.confidence * 100)}%</span>
              <span>Risk factors: {item.risk.factors.join(", ") || "none"}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
