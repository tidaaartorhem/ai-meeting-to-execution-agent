"""dates.py — relative due-date parsing + the disclosed replay calendar.

Replay calendar: the 171 meetings are placed on sequential weekdays ending
Friday 2026-10-09, in sorted meeting-id order. "Today" is fixed at
2026-10-12 (a Monday). This is disclosed in the README and the UI: it makes
due-date parsing and overdue computation deterministic on real 2006 speech.
"""
import datetime as dt
import re

REPLAY_TODAY = dt.date(2026, 10, 12)
LAST_MEETING_DATE = dt.date(2026, 10, 9)  # a Friday

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"]


def meeting_dates(meeting_id_list):
    """{meeting_id: date} — sequential weekdays, latest meeting last."""
    dates = {}
    d = LAST_MEETING_DATE
    for mid in sorted(meeting_id_list, reverse=True):
        dates[mid] = d
        # step back one weekday
        d -= dt.timedelta(days=1)
        while d.weekday() > 4:  # skip weekends backwards
            d -= dt.timedelta(days=1)
    return dates


def _next_weekday(after, name):
    target = WEEKDAYS.index(name)
    delta = (target - after.weekday()) % 7
    if delta == 0:
        delta = 7
    return after + dt.timedelta(days=delta)


# (compiled pattern, kind, date_fn)
_RULES = [
    (re.compile(r"\bbefore the next meeting\b|\bby next time\b|\bfor next time\b"
                r"|\bbefore we meet again\b", re.I), "next-meeting",
     lambda d: d + dt.timedelta(days=1)),
    (re.compile(r"\bin thirty minutes\b|\bin an hour\b|\bthis afternoon\b"
                r"|\bby the end of the day\b|\btoday\b", re.I), "today",
     lambda d: d),
    (re.compile(r"\btomorrow\b", re.I), "tomorrow",
     lambda d: d + dt.timedelta(days=1)),
    (re.compile(r"\bnext week\b", re.I), "next-week",
     lambda d: d + dt.timedelta(days=7)),
    (re.compile(r"\bin (?:a|one) week\b", re.I), "weeks-out",
     lambda d: d + dt.timedelta(days=7)),
    (re.compile(r"\bin two weeks\b|\bin a fortnight\b", re.I), "weeks-out",
     lambda d: d + dt.timedelta(days=14)),
    (re.compile(r"\bby the end of the week\b", re.I), "end-of-week",
     lambda d: _next_weekday(d, "friday")),
    (re.compile(r"\bend of the month\b", re.I), "month-end",
     lambda d: (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
               - dt.timedelta(days=1)),
]

_WEEKDAY_RE = re.compile(
    r"\b(?:by|on)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.I)


def parse_due(text, meeting_date):
    """Return {'raw', 'date' (ISO), 'kind'} or None."""
    for pat, kind, fn in _RULES:
        m = pat.search(text)
        if m:
            return {"raw": m.group(0), "date": fn(meeting_date).isoformat(),
                    "kind": kind}
    m = _WEEKDAY_RE.search(text)
    if m:
        raw = m.group(0)
        return {"raw": raw,
                "date": _next_weekday(meeting_date, m.group(1).lower()).isoformat(),
                "kind": "weekday"}
    return None
