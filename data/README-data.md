# Data provenance

## AMI Meeting Corpus (real research data)

The transcripts replayed by this project come from the **AMI Meeting Corpus**,
a public research corpus of 171 scenario meetings recorded in 2006 (Edinburgh).
Each meeting is a small team designing a new TV remote control; the manual
transcripts are the human-transcribed record of what was actually said.

- Mirror used at build time: https://github.com/gcunhase/AMICorpusXML
- Files: `data/ami-transcripts/<MEETING>.transcript.txt` — 171 merged transcripts
  (one paragraph per speaker turn; speakers not labeled in the merged files, so
  the pipeline labels them SPK-A..D by turn order).
- Speaker-separated versions also exist upstream at
  `data/ami-transcripts-speaker/<MEETING>.<A-D>.transcript.txt` (not bundled;
  the merged files are sufficient for turn-order speaker labeling).
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
