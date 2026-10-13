"""evaluate.py — golden-set precision/recall for extract.py.

data/golden-set.csv holds ~80 sentences hand-labeled during the build
(sentence, label) with label 1 = action item, 0 = not an action item.
Sentences were sampled half from rule hits (to catch false positives) and
half from rule misses (to catch false negatives).
"""
import csv
import os

from . import extract as extract_mod

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(REPO, "data", "golden-set.csv")


def load_golden():
    rows = []
    with open(GOLDEN, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["sentence"], int(r["label"])))
    return rows


def run(owner_map=None, meeting_date=None):
    """owner_map/meeting_date only affect owner/due fields; prediction is
    rule-hit vs no-hit, so pass a neutral map for eval."""
    import datetime as dt
    owner_map = owner_map or {"speakers": {}, "names": [], "roles": {}}
    meeting_date = meeting_date or dt.date(2026, 10, 1)
    tp = fp = fn = tn = 0
    for sentence, label in load_golden():
        hit = extract_mod.extract_sentence(sentence, "SPK-A", owner_map,
                                            meeting_date)
        pred = 1 if hit else 0
        if pred and label:
            tp += 1
        elif pred and not label:
            fp += 1
        elif not pred and label:
            fn += 1
        else:
            tn += 1
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "n": n, "true_positives": tp, "false_positives": fp,
        "false_negatives": fn, "true_negatives": tn,
        "precision": round(precision, 3), "recall": round(recall, 3),
        "note": ("golden set of %d hand-labeled sentences (half rule hits, "
                 "half misses); prediction = any extraction rule fires" % n),
    }
