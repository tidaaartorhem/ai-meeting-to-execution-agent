"""extract.py — ordered-rule action-item extraction at sentence level.

Deterministic, no models, no external calls. Rules fire in order; the first
match wins per sentence. Each item carries owner, evidence quote, meeting id,
confidence, and the rule that fired.
"""
import re

from . import dates as dates_mod
from . import owners as owners_mod

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
FILLER_LEAD = re.compile(
    r"^(?:(?:um|uh|er|ah|yes|mm-hmm?|yeah|yep|okay|ok|right|well|so|and|but|like|"
    r"actually|anyway|alright|sure|great|hi|hello)[,.\s]+)+", re.I)

# (rule_name, compiled pattern, confidence)
RULES = [
    ("action-marker",
     re.compile(r"\baction\s*item\b|\baction\s*:|\btodo\b|\bto-?do\b"
                r"|\bfollow[- ]up\b", re.I), 0.80),
    ("i-commitment",
     re.compile(r"\bi['\u2019]ll\b|\bi will\b|\bi am going to\b"
                r"|\bi['\u2019]?m gonna\b", re.I), 0.90),
    ("i-obligation",
     re.compile(r"\bi have to\b|\bi need to\b", re.I), 0.70),
    ("you-commitment",
     re.compile(r"\byou need to\b|\byou should\b|\byou have to\b|\byou must\b"
                r"|\byou['\u2019]?re going to\b|\byou['\u2019]?re gonna\b"
                r"|\bcan you\b|\bcould you\b|\bmake sure you\b|\bplease\b",
                re.I), 0.75),
    ("we-commitment",
     re.compile(r"\bwe need to\b|\bwe should\b|\bwe have to\b|\bwe must\b"
                r"|\bwe['\u2019]ll\b|\bwe will\b|\blet['\u2019]s\b", re.I),
     0.65),
    ("deadline-marker",
     re.compile(r"\bbefore the next meeting\b|\bby next time\b|\bfor next time\b"
                r"|\bbefore we meet again\b", re.I), 0.70),
    ("third-commitment",
     re.compile(r"\bhe['\u2019]ll\b|\bshe['\u2019]ll\b|\bhe will\b"
                r"|\bshe will\b", re.I), 0.60),
    ("need-to",
     re.compile(r"\bneed(?:s)? to\b", re.I), 0.60),
]

# owner resolution per rule: (fallback_to_speaker)
_OWNER_MODE = {
    "action-marker": True,
    "i-commitment": True,
    "i-obligation": True,
    "you-commitment": False,   # "you" without a name -> team can't tell who
    "we-commitment": False,    # team-owned -> Unassigned by design
    "deadline-marker": True,
    "third-commitment": True,
    "need-to": True,
}


def sentences_of(text):
    return [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]


def clean(sentence):
    s = FILLER_LEAD.sub("", sentence).strip()
    return re.sub(r"\s+", " ", s)


def extract_sentence(sentence, speaker, owner_map, meeting_date):
    """Return an item dict or None."""
    if len(sentence.split()) < 4:
        return None
    for rule_name, pat, conf in RULES:
        if pat.search(sentence):
            owner, _ = owners_mod.resolve_owner(
                sentence, speaker, owner_map,
                fallback_to_speaker=_OWNER_MODE[rule_name])
            return {
                "text": clean(sentence),
                "quote": sentence.strip(),
                "rule": rule_name,
                "confidence": conf,
                "owner": owner,
                "due": dates_mod.parse_due(sentence, meeting_date),
            }
    return None


def extract_meeting(meeting_id, turns, owner_map, meeting_date):
    items = []
    for t in turns:
        for si, s in enumerate(sentences_of(t["text"])):
            item = extract_sentence(s, t["speaker"], owner_map, meeting_date)
            if item:
                item.update({
                    "id": f"{meeting_id}-t{t['idx']:02d}-s{si:02d}",
                    "meeting": meeting_id,
                    "meeting_date": meeting_date.isoformat(),
                    "speaker": t["speaker"],
                })
                items.append(item)
    return items
