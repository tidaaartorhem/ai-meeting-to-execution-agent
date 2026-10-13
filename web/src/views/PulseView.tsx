import type { EvalData, Pulse } from "../types";
import { ItemRow } from "../components/ItemRow";

export default function PulseView({ pulse, evalData }: { pulse: Pulse; evalData: EvalData }) {
  return (
    <div>
      <h3 className="section-title">Weekly pulse · {pulse.replay_today}</h3>
      <div className="summary-grid">
        <div className="stat">
          <div className="stat-num">{pulse.meetings}</div>
          <div className="stat-label">meetings</div>
        </div>
        <div className="stat">
          <div className="stat-num">{pulse.items}</div>
          <div className="stat-label">items extracted</div>
        </div>
        <div className="stat">
          <div className="stat-num">{pulse.overdue}</div>
          <div className="stat-label">overdue</div>
        </div>
        <div className="stat">
          <div className="stat-num">{pulse.ownerless}</div>
          <div className="stat-label">ownerless</div>
        </div>
      </div>

      <h4 className="section-title">Do first — top {pulse.do_first.length}</h4>
      <div className="item-list">
        {pulse.do_first.map((i) => (
          <ItemRow key={i.id} item={i} replayToday={pulse.replay_today} />
        ))}
      </div>

      <h4 className="section-title">Owner digest</h4>
      <table className="data-table">
        <thead>
          <tr>
            <th>Owner</th>
            <th>Open</th>
            <th>Overdue</th>
            <th>No due date</th>
            <th>Overloaded</th>
          </tr>
        </thead>
        <tbody>
          {pulse.owner_digest.map((o) => (
            <tr key={o.name}>
              <td>
                <strong>{o.name}</strong>
              </td>
              <td>{o.open}</td>
              <td>{o.overdue}</td>
              <td>{o.no_due}</td>
              <td>{o.overloaded ? "yes" : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4 className="section-title">Questions to resolve</h4>
      <div className="questions">
        {pulse.questions.map((q) => (
          <div key={q.id} className="question">
            <div className="question-text">“{q.text}”</div>
            <div className="question-meta">
              {q.id} · owner: {q.owner} · {q.reason}
            </div>
          </div>
        ))}
      </div>

      <h4 className="section-title">Extraction quality</h4>
      <p className="footnote">
        Precision {evalData.precision.toFixed(3)} · recall {evalData.recall.toFixed(3)} —{" "}
        {evalData.true_positives} true positives, {evalData.false_positives} false positives,{" "}
        {evalData.false_negatives} false negatives on {evalData.note}.
      </p>

      <h4 className="section-title">How this brief is computed</h4>
      <p className="footnote">
        This brief is produced by deterministic rules, no model. Sentences are matched against an
        ordered rule list (action markers, commitments, deadlines), owners are assigned by
        sentence pattern, due dates are parsed from time expressions, and each item is scored 0–100
        from fixed weights: no owner +35, no due date +25, vague verb +15, overdue +30. Tiers are
        0–29 SAFE, 30–54 WATCH, 55–79 AT RISK, 80–100 CRITICAL. Overdue means the due date is
        before {pulse.replay_today}.
      </p>
    </div>
  );
}
