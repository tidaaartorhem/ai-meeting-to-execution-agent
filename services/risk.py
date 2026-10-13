"""risk.py — deterministic 0-100 risk score per action item.

Factors (additive, capped at 100):
  no owner            +35
  no due date         +25
  vague verb          +15  (think about / look into / sort out / consider /
                           figure out / maybe / somehow / at some point)
  overdue             +30  (due date < replay "today")
  owner overloaded    +10  (>= 4 open items for the same owner)
  stale meeting       +10  (meeting more than 5 days before "today")

Tiers: 0-29 SAFE / 30-54 WATCH / 55-79 AT RISK / 80-100 CRITICAL.
"""
import datetime as dt

VAGUE = ["think about", "look into", "sort out", "consider", "figure out",
         "maybe", "somehow", "at some point", "kind of", "sort of"]
OVERLOAD_THRESHOLD = 4
STALE_DAYS = 5


def is_overdue(item, today):
    due = item.get("due")
    if not due:
        return False
    return dt.date.fromisoformat(due["date"]) < today


def score(item, owner_open_counts, today):
    factors = []
    s = 0
    if item["owner"] == "Unassigned":
        s += 35
        factors.append("no owner")
    if not item.get("due"):
        s += 25
        factors.append("no due date")
    low = item["text"].lower()
    if any(v in low for v in VAGUE):
        s += 15
        factors.append("vague")
    if is_overdue(item, today):
        s += 30
        factors.append("overdue")
    if item["owner"] != "Unassigned" and \
            owner_open_counts.get(item["owner"], 0) >= OVERLOAD_THRESHOLD:
        s += 10
        factors.append("owner overloaded")
    meeting_date = dt.date.fromisoformat(item["meeting_date"])
    if (today - meeting_date).days > STALE_DAYS:
        s += 10
        factors.append("stale")
    return {"score": min(s, 100), "tier": tier(min(s, 100)), "factors": factors}


def tier(score):
    if score >= 80:
        return "CRITICAL"
    if score >= 55:
        return "AT RISK"
    if score >= 30:
        return "WATCH"
    return "SAFE"


def apply(items, today):
    counts = {}
    for it in items:
        if it["owner"] != "Unassigned":
            counts[it["owner"]] = counts.get(it["owner"], 0) + 1
    for it in items:
        it["risk"] = score(it, counts, today)
    return items
