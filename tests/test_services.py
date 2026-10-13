"""pytest suite for the Followthrough deterministic pipeline."""
import datetime as dt
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import dates as dates_mod
from services import evaluate as evaluate_mod
from services import extract as extract_mod
from services import ingest as ingest_mod
from services import owners as owners_mod
from services import risk as risk_mod
from services import pulse as pulse_mod

MDATE = dt.date(2026, 9, 1)  # a Tuesday
TODAY = dt.date(2026, 10, 12)
OMAP = {"speakers": {"SPK-A": {"name": "Laura", "role": "project manager"},
                     "SPK-B": {"name": "David", "role": "industrial designer"}},
        "names": ["Laura", "David"],
        "roles": {"project manager": "Laura", "industrial designer": "David"}}


def x(sent, speaker="SPK-A"):
    return extract_mod.extract_sentence(sent, speaker, OMAP, MDATE)


# ---- extraction rules ----

def test_i_commitment_owner_is_speaker():
    it = x("I'll send the slides before the next meeting.")
    assert it["rule"] == "i-commitment"
    assert it["owner"] == "Laura"
    assert it["confidence"] == 0.90


def test_you_commitment_name_mention_wins():
    it = x("David, you need to finish the working design.")
    assert it["rule"] == "you-commitment"
    assert it["owner"] == "David"


def test_you_commitment_role_mention():
    it = x("as the industrial designer, you're gonna be working on the working design")
    assert it["owner"] == "David"


def test_you_commitment_no_name_is_unassigned():
    it = x("you should check the cost figures")
    assert it["owner"] == "Unassigned"


def test_we_commitment_is_team_owned():
    it = x("we need to finalize the button layout")
    assert it["rule"] == "we-commitment"
    assert it["owner"] == "Unassigned"


def test_action_marker():
    it = x("Action: Laura to circulate the cost breakdown")
    assert it["rule"] == "action-marker"
    assert it["owner"] == "Laura"


def test_deadline_marker():
    it = x("we should have the sketches ready before the next meeting")
    assert it["due"]["kind"] == "next-meeting"


def test_no_false_positive_on_well():
    assert x("Well, my favourite animal would be a monkey.") is None


def test_no_false_positive_on_hell_or_lets():
    assert x("what the hell is that sketch supposed to be") is None
    assert x("he lets the team decide on the colour") is None


def test_short_sentences_skipped():
    assert x("I will go.") is None


# ---- due dates ----

def test_due_next_meeting():
    d = dates_mod.parse_due("ready before the next meeting", MDATE)
    assert d["date"] == "2026-09-02" and d["kind"] == "next-meeting"


def test_due_by_friday():
    d = dates_mod.parse_due("I'll have it by Friday", MDATE)  # Tue -> Fri
    assert d["date"] == "2026-09-04" and d["kind"] == "weekday"


def test_due_friday_from_friday_rolls_forward():
    d = dates_mod.parse_due("by Friday", dt.date(2026, 9, 4))
    assert d["date"] == "2026-09-11"


def test_due_two_weeks():
    d = dates_mod.parse_due("in two weeks we review", MDATE)
    assert d["date"] == "2026-09-15"


def test_due_tomorrow_and_today():
    assert dates_mod.parse_due("tomorrow", MDATE)["date"] == "2026-09-02"
    assert dates_mod.parse_due("I'll do it today", MDATE)["kind"] == "today"


def test_due_none():
    assert dates_mod.parse_due("maybe we could try a touchscreen", MDATE) is None


def test_replay_calendar_is_sequential_weekdays():
    mids = ["M%03d" % i for i in range(10)]
    ds = dates_mod.meeting_dates(mids)
    assert ds["M009"] == dt.date(2026, 10, 9)
    assert all(d.weekday() < 5 for d in ds.values())
    assert ds["M008"] < ds["M009"]


# ---- owners ----

def test_intro_parsing():
    turns = [{"speaker": "SPK-B",
              "text": "I'm Laura and I'm the project manager. Welcome everyone."}]
    m = owners_mod.build_map(turns)
    assert m["speakers"]["SPK-B"]["name"] == "Laura"
    assert m["speakers"]["SPK-B"]["role"] == "project manager"


def test_intro_with_filler():
    turns = [{"speaker": "SPK-D",
              "text": "And I'm Andrew and I'm uh our marketing expert. Right."}]
    m = owners_mod.build_map(turns)
    assert m["speakers"]["SPK-D"]["name"] == "Andrew"
    assert "marketing" in m["speakers"]["SPK-D"]["role"]


def test_unknown_speaker_unassigned():
    owner, _ = owners_mod.resolve_owner(
        "you should check this", "SPK-Z",
        {"speakers": {}, "names": [], "roles": {}}, fallback_to_speaker=False)
    assert owner == "Unassigned"


# ---- risk ----

def base_item(**kw):
    it = {"id": "t", "meeting": "M", "meeting_date": "2026-10-10",
          "owner": "Laura", "text": "I'll send the cost breakdown",
          "due": {"raw": "tomorrow", "date": "2026-10-11", "kind": "tomorrow"},
          "confidence": 0.9, "rule": "i-commitment"}
    it.update(kw)
    return it


def test_risk_ownerless_dateless():
    r = risk_mod.score(base_item(owner="Unassigned", due=None), {}, TODAY)
    assert r["score"] == 60 and r["tier"] == "AT RISK"
    assert set(r["factors"]) == {"no owner", "no due date"}


def test_risk_tier_boundaries():
    assert risk_mod.tier(0) == "SAFE" and risk_mod.tier(29) == "SAFE"
    assert risk_mod.tier(30) == "WATCH" and risk_mod.tier(54) == "WATCH"
    assert risk_mod.tier(55) == "AT RISK" and risk_mod.tier(79) == "AT RISK"
    assert risk_mod.tier(80) == "CRITICAL" and risk_mod.tier(100) == "CRITICAL"


def test_risk_overdue_and_stale_and_vague():
    it = base_item(owner="Unassigned", due=None,
                   meeting_date="2026-10-01",
                   text="we should maybe think about the remote")
    r = risk_mod.score(it, {}, TODAY)
    # 35 + 25 + 15 vague + 10 stale = 85 (not overdue: no due date)
    assert r["score"] == 85 and r["tier"] == "CRITICAL"


def test_risk_overloaded_owner():
    it = base_item()
    r = risk_mod.score(it, {"Laura": 4}, TODAY)
    assert r["score"] == 10 and "owner overloaded" in r["factors"]


def test_risk_capped_at_100():
    it = base_item(owner="Unassigned", due={"raw": "x", "date": "2026-01-01",
                                            "kind": "today"},
                   meeting_date="2026-01-01", text="maybe think about stuff")
    r = risk_mod.score(it, {"Unassigned": 99}, TODAY)
    assert r["score"] == 90  # 35 no-owner + 15 vague + 30 overdue + 10 stale


def test_overdue_detection():
    assert risk_mod.is_overdue(base_item(), TODAY)  # due 2026-10-11 < 10-12
    assert not risk_mod.is_overdue(
        base_item(due={"raw": "x", "date": "2026-10-20", "kind": "weekday"}),
        TODAY)
    assert not risk_mod.is_overdue(base_item(due=None), TODAY)


# ---- pulse + ingest + eval sanity ----

def test_pulse_do_first_ranking():
    a = base_item(id="a", owner="Unassigned", due=None)
    b = base_item(id="b")
    risk_mod.apply([a, b], TODAY)
    top = pulse_mod.do_first([a, b], n=2)
    assert [t["id"] for t in top] == ["a", "b"]


def test_ingest_lists_171_meetings():
    assert len(ingest_mod.meeting_ids()) == 171


def test_eval_runs_and_reports_numbers():
    res = evaluate_mod.run()
    assert res["n"] == 80
    assert 0.0 <= res["precision"] <= 1.0
    assert 0.0 <= res["recall"] <= 1.0
    assert res["true_positives"] + res["false_negatives"] > 0
