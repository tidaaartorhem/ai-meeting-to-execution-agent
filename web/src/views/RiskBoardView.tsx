import { useMemo, useState } from "react";
import type { ExecItem, Pulse } from "../types";
import { isOverdue } from "../types";
import { ItemRow } from "../components/ItemRow";

interface Bucket {
  key: string;
  title: string;
  description: string;
}

const BUCKETS: Bucket[] = [
  { key: "ownerless", title: "Ownerless", description: "Items with no named owner" },
  { key: "dateless", title: "Dateless", description: "Items with no due date" },
  { key: "overdue", title: "Overdue", description: "Due date before today" },
  { key: "overloaded", title: "Overloaded owners", description: "Owners flagged overloaded" },
];

export default function RiskBoardView({ items, pulse }: { items: ExecItem[]; pulse: Pulse }) {
  const [open, setOpen] = useState<string | null>("ownerless");

  const bucketItems = useMemo<Record<string, ExecItem[]>>(() => {
    const ownerless = items.filter((i) => i.owner === "Unassigned");
    const dateless = items.filter((i) => i.due === null);
    const overdue = items.filter((i) => isOverdue(i, pulse.replay_today));
    const overloadedNames = new Set(pulse.owner_digest.filter((o) => o.overloaded).map((o) => o.name));
    const overloaded = items.filter((i) => overloadedNames.has(i.owner));
    return { ownerless, dateless, overdue, overloaded };
  }, [items, pulse]);

  const overloadedOwners = pulse.owner_digest.filter((o) => o.overloaded);

  return (
    <div className="board-grid">
      {BUCKETS.map((b) => {
        const list = bucketItems[b.key];
        const isOpen = open === b.key;
        return (
          <div key={b.key} className="bucket">
            <button className="bucket-head" onClick={() => setOpen(isOpen ? null : b.key)}>
              <span className="bucket-title">
                {b.title} <span className="bucket-count">{list.length}</span>
              </span>
              <span className="bucket-desc">{b.description}</span>
              <span className="bucket-toggle">{isOpen ? "−" : "+"}</span>
            </button>
            {isOpen && (
              <div className="bucket-body">
                {b.key === "overloaded" && (
                  <div className="owner-lines">
                    {overloadedOwners.map((o) => (
                      <div key={o.name} className="owner-line">
                        <strong>{o.name}</strong> — {o.open} open · {o.overdue} overdue · {o.no_due}{" "}
                        no due date
                      </div>
                    ))}
                    {overloadedOwners.length === 0 && <p className="empty">No overloaded owners.</p>}
                  </div>
                )}
                <div className="item-list">
                  {list
                    .sort((a, b2) => b2.risk.score - a.risk.score)
                    .map((i) => (
                      <ItemRow key={i.id} item={i} replayToday={pulse.replay_today} />
                    ))}
                </div>
                {list.length === 0 && <p className="empty">Nothing in this bucket.</p>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
