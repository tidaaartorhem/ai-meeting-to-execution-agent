# Followthrough — the meeting execution board

Every meeting ends the same way: a handful of verbal commitments ("you'll work on the working design", "we need this before the next meeting") that live and die in someone's notes. A week later nobody remembers who owned what, by when, or what was even agreed. That is the execution gap, and it is where follow-through goes to die.

Followthrough closes it with a deterministic pipeline. It replays **171 real meeting transcripts** and turns each one into a ranked execution board: every action item with an owner, a parsed due date, a risk score, and the exact quote as evidence. No models, no black boxes, no API calls. The same ordered rules that process the corpus also run in your browser on the paste-a-transcript tab, so anything you paste gets the same treatment instantly.

**Live:** https://ai-meeting-to-execution-agent.web.app
**Repo:** https://github.com/tidaaartorhem/ai-meeting-to-execution-agent

## What the replay found

Running the pipeline over all 171 meetings produced **6,503 action items** (38 per meeting). The headline numbers are the product's thesis, stated plainly:

- **95.9% ownerless** — no name could be resolved for the commitment
- **98.7% dateless** — no due date was stated or parseable
- **1.3% overdue** against the replay calendar (most items have no date to be overdue against)
- **760 CRITICAL** items, **5,496 AT RISK**, **247 WATCH**

That is not a pipeline failure. The corpus is real meetings among colleagues who never introduce themselves and rarely state dates out loud, so most verbal commitments genuinely have no owner and no date. The board makes that visible instead of letting it dissolve into notes.

## Real data

The transcripts are the **AMI Meeting Corpus**: 171 scenario meetings recorded in 2006 at the University of Edinburgh, in which small teams design a new TV remote control. The pipeline uses the public mirror at https://github.com/gcunhase/AMICorpusXML (`data/ami-transcripts-speaker/`, 687 speaker files; the merged `data/ami-transcripts/` copies are kept as the archival source). Full provenance and license notes: `data/README-data.md`.

Two honest disclosures:

1. **These are 2006 scenario meetings**, not live business meetings. The remote-control design brief, the roles (project manager, industrial designer, marketing, UI), and the speech patterns are all from the corpus. Nothing here is current.
2. **Replay calendar.** The corpus has no usable dates, so each meeting is placed on sequential weekdays ending Friday 2026-10-09 (in sorted meeting-id order), and "today" is fixed at Monday 2026-10-12. That makes due-date parsing and overdue computation deterministic. The UI states the replay date wherever dates appear.

## How the pipeline works

`services/`, pure Python stdlib, fully deterministic. Run it with `python -m services.main` from the repo root; it writes `web/public/*.json` (items, meetings, owners, pulse, eval) plus `data/pulse.md`.

**ingest.py** — Loads the speaker-separated transcript files (one segment per speaker, labeled with the real speaker key SPK-A..D, occasionally SPK-E). Build-time discovery, documented in `data/README-data.md`: this mirror's "merged" files are *not* chronological turns. Each merged paragraph is byte-identical to one speaker's entire concatenated contribution, so the pipeline reads the speaker files directly, which gives better attribution than turn-order guessing.

**owners.py** — Resolves speakers to real names from self-introductions ("I'm Laura and I'm the project manager"), pooled per meeting *series* (ES2002a-d is one team; speaker letters were verified 100% stable within series across all 22 series with introductions). Per-sentence owner resolution order: explicit name mention, role mention ("as the industrial designer, you're..."), sentence-initial vocative ("David, can you..."), then the speaker's own name. Falls back to "Unassigned". Name candidates are validated against a stoplist so fragments like "my name is not..." never become owners.

**extract.py** — Ordered rule extraction at sentence level; the first matching rule wins. Each item carries the owner, the evidence quote, the meeting id, a confidence, and the rule that fired:

| Rule | Pattern family | Confidence |
|---|---|---|
| action-marker | "action:", "todo", "follow up" | 0.80 |
| i-commitment | "I'll", "I will", "I'm gonna" | 0.90 |
| i-obligation | "I have to", "I need to" | 0.70 |
| you-commitment | "you need to", "can you", "you're gonna" | 0.75 |
| we-commitment | "we need to", "we should", "let's" | 0.65 |
| deadline-marker | "before the next meeting", "by next time" | 0.70 |
| third-commitment | "he'll", "she will" | 0.60 |
| need-to | "needs to", "need to" | 0.60 |

Contraction patterns require the apostrophe ("we'll", never "we'll?"): an optional apostrophe matches ordinary words ("Well", "hell"). There is a regression test for exactly that.

**dates.py** — Relative due-date parsing against the meeting date: "before the next meeting" → +1 day, "today"/"this afternoon" → +0, "tomorrow" → +1, "by Friday" → next Friday, "next week" → +7, "in two weeks" → +14, "end of the month" → month end.

**risk.py** — Deterministic 0-100 score: no owner +35, no due date +25, vague verb +15, overdue +30, overloaded owner (4+ open items) +10, stale meeting (>5 days past) +10. Tiers: SAFE 0-29, WATCH 30-54, AT RISK 55-79, CRITICAL 80-100.

**pulse.py** — The weekly execution pulse: top-10 "do first" list by risk, per-owner digest (open/overdue/dateless, overloaded flags), and "questions to resolve" (team-owned, ownerless, dateless, or low-confidence items a human must decide on). Emitted as markdown (`data/pulse.md`) and JSON for the UI.

**evaluate.py** — Golden-set evaluation. `data/golden-set.csv` holds 80 sentences hand-labeled during the build (half sampled from rule hits, half from misses), labeled 1 = action item. Result: **precision 0.50, recall 1.00**. Read honestly: the rules catch essentially every real commitment (nothing meaningful slips through), but about half of what fires is discussion rather than a trackable task ("we should think about...", "let's carry on"). Two patterns ("I have to", "I need to") were added after reviewing the golden set; that is disclosed here rather than hidden.

## The web app

`web/` — React + TypeScript + Vite, light mode. Five views, all rendered from the pipeline JSON:

- **Execution queue** — all 6,503 items ranked by risk, with tier chips, owner, due date, evidence quote, and the rule that fired. Filter by tier, search by owner or text.
- **Risk board** — four buckets: ownerless, dateless, overdue, overloaded owners, with counts.
- **Meetings** — per-meeting extraction summary; click through to a meeting's items.
- **Weekly pulse** — the deterministic brief rendered as a readable page.
- **Paste a transcript** — the same ordered rules compiled to TypeScript run entirely in the browser on pasted notes: instant board, same risk math. Speaker slots rotate per paragraph and "I'm ..." intros name them.

## Run it

```bash
pip install -r requirements.txt
python -m services.main     # replay the corpus -> web/public/*.json
python -m pytest tests/ -q  # 30 tests
cd web && npm install && npm run build && npx vitest run  # 13 tests
```

Deploy (Firebase Hosting, project `portfolio-3da31`):

```bash
cd web && npm run build
firebase deploy --only hosting --project portfolio-3da31
```

## Layout

```
services/        # the deterministic pipeline (ingest, owners, extract, dates, risk, pulse, evaluate, main)
web/             # React + TypeScript frontend (Vite); web/public/*.json is pipeline output
web/src/extraction.ts  # the same rules in TypeScript for the paste-a-transcript tab
data/            # AMI transcripts (speaker-separated + merged archival), golden set, pulse.md
tests/           # 30 pytest tests
scripts/         # golden-set sampling/labeling helpers, smoke test
```

Built as one of twenty daily AI-automation builds. Real data, deterministic rules, honest numbers.
