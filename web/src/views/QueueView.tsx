import { useMemo, useState } from "react";
import type { ExecItem, Tier } from "../types";
import { ItemRow } from "../components/ItemRow";

const TIERS: Tier[] = ["SAFE", "WATCH", "AT RISK", "CRITICAL"];

export default function QueueView({ items, replayToday }: { items: ExecItem[]; replayToday: string }) {
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [ownerQuery, setOwnerQuery] = useState("");
  const [textQuery, setTextQuery] = useState("");

  const ranked = useMemo(() => {
    const q = textQuery.trim().toLowerCase();
    const oq = ownerQuery.trim().toLowerCase();
    return [...items]
      .filter((i) => (tierFilter === "ALL" ? true : i.risk.tier === tierFilter))
      .filter((i) => (oq === "" ? true : i.owner.toLowerCase().includes(oq)))
      .filter((i) => (q === "" ? true : (i.text + " " + i.quote).toLowerCase().includes(q)))
      .sort((a, b) => b.risk.score - a.risk.score);
  }, [items, tierFilter, ownerQuery, textQuery]);

  return (
    <div>
      <div className="filters">
        <label>
          Tier
          <select value={tierFilter} onChange={(e) => setTierFilter(e.target.value)}>
            <option value="ALL">All</option>
            {TIERS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label>
          Owner
          <input
            type="text"
            placeholder="search owner…"
            value={ownerQuery}
            onChange={(e) => setOwnerQuery(e.target.value)}
          />
        </label>
        <label>
          Text
          <input
            type="text"
            placeholder="search text…"
            value={textQuery}
            onChange={(e) => setTextQuery(e.target.value)}
          />
        </label>
      </div>
      <p className="hint">
        {ranked.length} item{ranked.length === 1 ? "" : "s"} · ranked by risk score
      </p>
      <div className="item-list">
        {ranked.map((i) => (
          <ItemRow key={i.id} item={i} replayToday={replayToday} />
        ))}
      </div>
      {ranked.length === 0 && <p className="empty">No items match the current filters.</p>}
    </div>
  );
}
