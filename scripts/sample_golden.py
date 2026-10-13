"""Sample 80 candidate sentences for the hand-labeled golden set.

45 from extraction-rule hits (to catch false positives) + 35 from rule
misses (to catch false negatives). Deterministic seed. Output:
data/golden-candidates.txt — numbered sentences; label them into
data/golden-set.csv as (sentence, label) with label 1 = action item.
"""
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import ingest, owners, extract, dates

random.seed(20261013)
mids = ingest.meeting_ids()
mdates = dates.meeting_dates(mids)
hits, misses = [], []
for mid in mids:
    turns = ingest.load_turns(mid)
    omap = owners.build_map(turns)
    for t in turns:
        for s in extract.sentences_of(t["text"]):
            if len(s.split()) < 4:
                continue
            it = extract.extract_sentence(s, t["speaker"], omap, mdates[mid])
            (hits if it else misses).append(s.strip())

print(f"hits={len(hits)} misses={len(misses)}")
random.shuffle(hits)
random.shuffle(misses)
cands = [("HIT", s) for s in hits[:45]] + [("MISS", s) for s in misses[:35]]
random.shuffle(cands)
with open("data/golden-candidates.txt", "w", encoding="utf-8") as f:
    for i, (kind, s) in enumerate(cands, 1):
        f.write(f"[{i:02d}][{kind}] {s}\n")
print("wrote data/golden-candidates.txt:", len(cands))
