"""main.py — run the whole pipeline, write web/public/*.json.

Usage: python -m services.main   (from the repo root)
"""
import json
import os

from services import dates as dates_mod
from services import evaluate as evaluate_mod
from services import extract as extract_mod
from services import ingest as ingest_mod
from services import owners as owners_mod
from services import pulse as pulse_mod
from services import risk as risk_mod

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "web", "public")

TODAY = dates_mod.REPLAY_TODAY


def run():
    mids = ingest_mod.meeting_ids()
    print(f"{len(mids)} meetings")
    mdates = dates_mod.meeting_dates(mids)

    all_turns = {mid: ingest_mod.load_turns(mid) for mid in mids}
    series_maps = owners_mod.build_series_maps(all_turns)

    items, meetings, owner_rows = [], [], {}
    for mid in mids:
        turns = all_turns[mid]
        omap = series_maps[mid]
        mitems = extract_mod.extract_meeting(mid, turns, omap, mdates[mid])
        items.extend(mitems)
        overdue = sum(1 for it in mitems
                      if risk_mod.is_overdue(it, TODAY))
        meetings.append({
            "id": mid,
            "meeting_date": mdates[mid].isoformat(),
            "turns": len(turns),
            "items": len(mitems),
            "ownerless": sum(1 for it in mitems if it["owner"] == "Unassigned"),
            "dateless": sum(1 for it in mitems if not it.get("due")),
            "overdue": overdue,
        })

    risk_mod.apply(items, TODAY)
    # per-meeting aggregates after risk
    by_meeting = {}
    for it in items:
        by_meeting.setdefault(it["meeting"], []).append(it)
    for m in meetings:
        mis = by_meeting.get(m["id"], [])
        m["avg_risk"] = round(sum(i["risk"]["score"] for i in mis) / len(mis), 1) if mis else 0.0
        m["top_risks"] = [i["id"] for i in
                          sorted(mis, key=lambda x: -x["risk"]["score"])[:3]]

    for it in items:  # owner digest rows (also written standalone)
        o = it["owner"]
        a = owner_rows.setdefault(o, {"name": o, "open": 0, "overdue": 0,
                                      "no_due": 0, "meetings": set()})
        a["open"] += 1
        if risk_mod.is_overdue(it, TODAY):
            a["overdue"] += 1
        if not it.get("due"):
            a["no_due"] += 1
        a["meetings"].add(it["meeting"])
    owners = []
    for a in owner_rows.values():
        a["meetings"] = sorted(a["meetings"])
        a["overloaded"] = a["name"] != "Unassigned" and a["open"] >= 4
        owners.append(a)
    owners.sort(key=lambda a: -a["open"])

    pulse = pulse_mod.build(items, TODAY, TODAY.isoformat())
    pulse_json = {k: v for k, v in pulse.items() if k != "markdown"}
    try:
        eval_result = evaluate_mod.run()
    except FileNotFoundError:
        eval_result = {"n": 0, "precision": 0.0, "recall": 0.0,
                       "note": "golden set not yet labeled"}

    os.makedirs(OUT, exist_ok=True)
    payloads = {"items.json": items, "meetings.json": meetings,
                "owners.json": owners, "pulse.json": pulse_json,
                "eval.json": eval_result}
    for fname, payload in payloads.items():
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        print(f"wrote {fname}: {len(payload) if isinstance(payload, list) else 'obj'}")

    with open(os.path.join(REPO, "data", "pulse.md"), "w") as f:
        f.write(pulse["markdown"])

    print(f"items={len(items)} meetings={len(meetings)} "
          f"ownerless={sum(1 for i in items if i['owner']=='Unassigned')} "
          f"overdue={sum(1 for i in items if risk_mod.is_overdue(i, TODAY))} "
          f"precision={eval_result['precision']} recall={eval_result['recall']}")
    return payloads


if __name__ == "__main__":
    run()
