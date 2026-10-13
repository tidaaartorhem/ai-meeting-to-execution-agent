# Data provenance

## AMI Meeting Corpus (real research data)

The transcripts replayed by this project come from the **AMI Meeting Corpus**,
a public research corpus of 171 scenario meetings recorded in 2006 (Edinburgh).
Each meeting is a small team designing a new TV remote control; the manual
transcripts are the human-transcribed record of what was actually said.

- Mirror used at build time: https://github.com/gcunhase/AMICorpusXML
- Files: `data/ami-transcripts/<MEETING>.transcript.txt` — 171 merged transcripts
  (kept as the archival source).
- Speaker-separated versions at `data/ami-transcripts-speaker/<MEETING>.<A-D>.transcript.txt`
  — **these are what the pipeline actually uses**.

## Build-time discovery: merged files are per-speaker concatenations

The brief assumed each paragraph of a merged transcript was a chronological
speaker turn. Spot-checking at build time (e.g. `ES2002a`) proved otherwise:
each merged paragraph is byte-identical to one speaker's entire concatenated
contribution (verified: merged paragraph lengths [426, 5312, 6678, 1256]
exactly match speaker files C, D, B, A). There is no chronological turn
structure in either version of this mirror. The pipeline therefore reads the
speaker-separated files directly — one segment per speaker (SPK-A..D,
occasionally SPK-E) — which gives *better* attribution than the brief's
turn-order guessing: owners resolve from each speaker's own self-introductions
("I'm Laura and I'm the project manager").
- Typical size: ~80 KB per meeting; ~14 MB total.
- License note: the AMI corpus is released for research use by the AMI
  consortium (see the mirror's README and http://groups.inf.ed.ac.uk/ami/corpus/).

## Honest framing

These are **scenario meetings from 2006** — remote-control design teams with
assigned roles (project manager, industrial designer, marketing, UI). The
pipeline treats them as a replay: it assigns each meeting a date on a disclosed
replay calendar (sequential weekdays ending Friday 2026-10-09; "today" is fixed
at 2026-10-12, disclosed in the README) so due-date parsing and overdue
computation are deterministic. Nothing here is live or current; it is a
demonstration of the extraction rules on real, messy human speech.
