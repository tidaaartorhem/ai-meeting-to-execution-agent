import csv
import re
import sys

sys.path.insert(0, ".")

# sentence -> label (1 = action item, 0 = not). Labeled by hand 2026-10-13.
LABELS = {
 1: 0,  2: 0,  3: 1,  4: 0,  5: 0,  6: 0,  7: 0,  8: 0,  9: 0, 10: 0,
11: 1, 12: 0, 13: 1, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 1, 20: 1,
21: 0, 22: 0, 23: 1, 24: 0, 25: 0, 26: 1, 27: 0, 28: 0, 29: 0, 30: 1,
31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 36: 0, 37: 0, 38: 1, 39: 1, 40: 0,
41: 1, 42: 1, 43: 0, 44: 1, 45: 0, 46: 0, 47: 0, 48: 0, 49: 1, 50: 0,
51: 1, 52: 0, 53: 1, 54: 0, 55: 0, 56: 0, 57: 0, 58: 1, 59: 0, 60: 0,
61: 0, 62: 0, 63: 0, 64: 0, 65: 1, 66: 0, 67: 1, 68: 0, 69: 1, 70: 0,
71: 1, 72: 0, 73: 0, 74: 0, 75: 1, 76: 0, 77: 1, 78: 0, 79: 0, 80: 0,
}

rows = []
for line in open("data/golden-candidates.txt", encoding="utf-8"):
    line = line.rstrip("\n")
    m = re.match(r"\[(\d+)\]\[(HIT|MISS)\] (.*)", line)
    assert m, line
    idx = int(m.group(1))
    rows.append((m.group(3), LABELS[idx]))

assert len(rows) == 80
with open("data/golden-set.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sentence", "label"])
    w.writerows(rows)
print("wrote data/golden-set.csv:", len(rows),
      "positives:", sum(l for _, l in rows))
