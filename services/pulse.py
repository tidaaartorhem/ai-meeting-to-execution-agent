"""pulse.py — deterministic weekly execution pulse.

- "do first": top-10 items by risk score (ties broken by earlier due date)
- owner digest: open / overdue / dateless counts per owner
- "questions to resolve": ambiguous items a human must decide on
Emits both markdown (readable brief) and JSON (for the web UI).
"""
import datetime as dt

from . import risk as risk_mod


def do_first(items, n=10):
    def key(it):
        due = it["due"]["date"] if it.get("due") else "9999-12-31"
        return (-it["risk"]["score"], due)
    return sorted(items, key=key)[:n]


def owner_digest(items, today):
    agg = {}
    for it in items:
        o = it["owner"]
        a = agg.setdefault(o, {"name": o, "open": 0, "overdue": 0, "no_due": 0,
                               "meetings": set()})
        a["open"] += 1
        if risk_mod.is_overdue(it, today):
            a["overdue"] += 1
        if not it.get("due"):
            a["no_due"] += 1
        a["meetings"].add(it["meeting"])
    out = []
    for a in agg.values():
        a["meetings"] = sorted(a["meetings"])
        a["overloaded"] = a["name"] != "Unassigned" and a["open"] >= 4
        out.append(a)
    return sorted(out, key=lambda a: (-a["overdue"], -a["open"]))


def questions_to_resolve(items, n=12):
    """Ambiguous items needing a human decision."""
    out = []
    for it in items:
        reasons = []
        if it["rule"] == "we-commitment":
            reasons.append("team-owned ('we') — no single owner")
        if it["owner"] == "Unassigned":
            reasons.append("no owner resolved")
        if not it.get("due"):
            reasons.append("no due date parsed")
        if it["confidence"] < 0.7:
            reasons.append(f"low rule confidence ({it['confidence']:.2f})")
        if reasons:
            out.append({"id": it["id"], "text": it["text"], "owner": it["owner"],
                        "reason": "; ".join(reasons)})
    out.sort(key=lambda q: (q["owner"] != "Unassigned", q["id"]))
    return out[:n]


def build(items, today, replay_today_iso):
    top = do_first(items)
    digest = owner_digest(items, today)
    questions = questions_to_resolve(items)
    overdue = sum(1 for it in items if risk_mod.is_overdue(it, today))
    ownerless = sum(1 for it in items if it["owner"] == "Unassigned")
    data = {
        "replay_today": replay_today_iso,
        "meetings": len({it["meeting"] for it in items}),
        "items": len(items),
        "overdue": overdue,
        "ownerless": ownerless,
        "do_first": top,
        "owner_digest": digest,
        "questions": questions,
    }
    lines = [
        "# Weekly execution pulse",
        f"_Deterministic brief · replay week ending {replay_today_iso} · "
        f"{len(items)} action items across {data['meetings']} meetings_",
        "",
        f"**Headline:** {overdue} overdue, {ownerless} ownerless, "
        f"{sum(1 for d in digest if d['overloaded'])} overloaded owners.",
        "",
        "## Do first (top risk)",
    ]
    for i, it in enumerate(top, 1):
        due = it["due"]["date"] if it.get("due") else "no date"
        lines.append(
            f"{i}. **{it['text']}** — {it['owner']}, due {due}, "
            f"{it['risk']['tier']} ({it['risk']['score']}) "
            f"[{it['meeting']}]")
    lines += ["", "## Owner digest"]
    for d in digest[:15]:
        flag = " OVERLOADED" if d["overloaded"] else ""
        lines.append(
            f"- **{d['name']}**: {d['open']} open, {d['overdue']} overdue, "
            f"{d['no_due']} dateless{flag}")
    lines += ["", "## Questions to resolve"]
    for q in questions:
        lines.append(f"- {q['text']} ({q['owner']}) — {q['reason']}")
    data["markdown"] = "\n".join(lines)
    return data
