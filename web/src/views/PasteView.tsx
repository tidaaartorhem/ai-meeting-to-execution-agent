import { useState } from "react";
import { extractFromTranscript, RULES, isoDate } from "../extraction";
import { ItemRow } from "../components/ItemRow";

const SAMPLE = `Priya here — I'm Priya, thanks for joining.

We need to finalize the vendor shortlist by Friday.

I'll send the revised deck tomorrow.

Can you look into the pricing model, David?

Let's sort out the migration timeline somehow.`;

export default function PasteView() {
  const [text, setText] = useState("");
  const [ran, setRan] = useState(false);
  const today = new Date();
  const todayISO = isoDate(today);

  const results = ran && text.trim() ? extractFromTranscript(text, { today }) : [];

  return (
    <div>
      <p className="hint">
        Paste rough notes. Each blank-line-separated paragraph is treated as a turn; speakers rotate
        Speaker 1–5, and an “I’m &lt;Name&gt;” self-intro names that speaker. The same ordered
        extraction rules as the pipeline run instantly in your browser.
      </p>
      <div className="paste-grid">
        <div>
          <textarea
            className="paste-area"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setRan(false);
            }}
            placeholder="Paste meeting notes here…"
            rows={12}
          />
          <div className="paste-actions">
            <button className="primary-btn" onClick={() => setRan(true)} disabled={!text.trim()}>
              Run extraction
            </button>
            <button
              className="link-btn"
              onClick={() => {
                setText(SAMPLE);
                setRan(false);
              }}
            >
              Load sample notes
            </button>
          </div>
        </div>
        <div>
          <h4 className="section-title">Rules</h4>
          <ol className="rules-list">
            {RULES.map((r) => (
              <li key={r.name}>
                <code>{r.name}</code>
              </li>
            ))}
          </ol>
          <p className="footnote">
            First matching rule wins per turn. Owner comes from a named person in the sentence or the
            speaker; “we” and ambiguous “you” become Unassigned. Risk: no owner +35, no due date +25,
            vague verb +15, overdue +30. Tiers: 0–29 SAFE, 30–54 WATCH, 55–79 AT RISK, 80–100
            CRITICAL. Stale items are ignored in this view.
          </p>
        </div>
      </div>

      {ran && (
        <div className="results">
          <h4 className="section-title">
            Extraction result — {results.length} item{results.length === 1 ? "" : "s"}
          </h4>
          {results.length > 0 ? (
            <div className="item-list">
              {results.map((i) => (
                <ItemRow key={i.id} item={i} replayToday={todayISO} showMeeting={false} />
              ))}
            </div>
          ) : (
            <p className="empty">
              No commitments detected. Try sentences like “I'll send the slides” or “we need to
              finalize the budget by Friday”.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
