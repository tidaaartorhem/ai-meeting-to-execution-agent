"""owners.py — per-meeting speaker -> real-name map from self-introductions.

The AMI teams introduce themselves at the start of early meetings
("I'm Laura and I'm the project manager"), so owners resolve to real names.
Falls back to "Unassigned" when no name can be determined.
"""
import re

# "I'm Laura and I'm the project manager" / "my name is David"
# Role is captured up to the sentence end, then cleaned of filler words.
INTRO_RE = re.compile(
    r"\bI['\u2019]?m\s+([A-Z][a-zA-Z]{1,20})\s+and\s+I['\u2019]?m\s+([^.!?]{3,80})"
)
MY_NAME_RE = re.compile(r"\bmy name is\s+([A-Z][a-zA-Z]{1,20})\b")
I_AM_RE = re.compile(r"\bI am\s+([A-Z][a-zA-Z]{1,20})\b")

GENERIC_WORDS = {"Um", "Uh", "And", "So", "Well", "Yeah", "Okay", "Right", "Hi",
                 "Hello", "Sure", "Great", "Alright", "Mm", "Hmm", "Ah", "Oh"}
# Extra guard: intro regexes can catch sentence fragments ("my name is not..").
NAME_STOP = GENERIC_WORDS | {
    "Not", "Name", "The", "This", "That", "These", "Those", "There", "They",
    "What", "When", "Where", "Which", "With", "From", "For", "Your", "Our",
    "Just", "Like", "Also", "Even", "Still", "Then", "Now", "Here", "Very",
    "More", "Most", "Some", "Such", "Only", "Over", "Under", "After",
    "Before", "Because", "While", "Project", "Manager", "Meeting",
}
NAME_RE = re.compile(r"^[A-Z][a-z]{1,15}$")


def valid_name(word):
    return bool(NAME_RE.match(word)) and word not in NAME_STOP
FILLER_WORDS = {"uh", "um", "er", "ah", "the", "our", "a", "an", "supposed",
                "just", "like", "really", "to", "be"}


def clean_role(raw):
    words = raw.lower().replace(",", " ").split()
    words = [w for w in words if w not in FILLER_WORDS]
    return " ".join(words[:4]) or None


FILLER_LEAD = re.compile(
    r"^(?:(?:um|uh|er|ah|yes|mm-hmm?|yeah|yep|okay|ok|right|well|so|and|but|like|"
    r"actually|anyway|alright|sure|great|hi|hello)[,.\s]+)+", re.I)
VOCATIVE_RE = re.compile(r"^([A-Z][a-z]{2,12}),\s+")
VOCATIVE_STOP = {"Well", "Okay", "Yeah", "Yes", "Right", "Now", "Still", "Then",
                 "Actually", "Anyway", "Alright", "Sure", "Great", "Hello",
                 "Listen", "Look", "Wait", "Sorry", "Thanks", "Please",
                 "Today", "Tomorrow", "Maybe"}


def vocative(sentence):
    """Sentence-initial addressed name ('David, can you ...'), or None."""
    s = FILLER_LEAD.sub("", sentence).strip()
    m = VOCATIVE_RE.match(s)
    if m and valid_name(m.group(1)) and m.group(1) not in VOCATIVE_STOP:
        return m.group(1)
    return None


def build_map(turns):
    """Return {'speakers': {SPK-A: {'name':..,'role':..}}, 'names': [...],
    'roles': {role_string: name}} for one meeting."""
    speakers, names, roles = {}, [], {}
    for t in turns:
        spk = t["speaker"]
        if spk in speakers:
            continue
        name, role = None, None
        m = INTRO_RE.search(t["text"])
        if m and valid_name(m.group(1)):
            name = m.group(1)
            role = clean_role(m.group(2))
        if not name:
            m = MY_NAME_RE.search(t["text"]) or I_AM_RE.search(t["text"])
            if m and valid_name(m.group(1)):
                name = m.group(1)
        if name:
            speakers[spk] = {"name": name, "role": role}
            names.append(name)
            if role:
                roles[role] = name
    return {"speakers": speakers, "names": names, "roles": roles}


def build_series_maps(all_turns):
    """Pool speaker->name intros across each meeting series.

    Verified at build time: within a series (e.g. ES2002a-d) speaker letters
    are 100% stable (22/22 series with intros), and each series is the same
    team across its meetings. If a series ever shows conflicting names for
    one letter, that series falls back to per-meeting maps.
    """
    per_meeting = {mid: build_map(turns) for mid, turns in all_turns.items()}
    series_of = {}
    for mid in all_turns:
        series_of.setdefault(mid[:-1], []).append(mid)
    out = {}
    for series, mids in series_of.items():
        merged = {"speakers": {}, "names": [], "roles": {}}
        conflict = False
        for mid in mids:
            for spk, info in per_meeting[mid]["speakers"].items():
                if spk in merged["speakers"]:
                    if merged["speakers"][spk]["name"] != info["name"]:
                        conflict = True
                else:
                    merged["speakers"][spk] = info
        if conflict:  # fall back to per-meeting maps for this series
            for mid in mids:
                out[mid] = per_meeting[mid]
            continue
        for spk, info in merged["speakers"].items():
            merged["names"].append(info["name"])
            if info["role"]:
                merged["roles"][info["role"]] = info["name"]
        for mid in mids:
            out[mid] = merged
    return out


def name_in_sentence(sentence, names):
    """First participant first-name mentioned in the sentence, else None."""
    for name in names:
        if re.search(r"\b" + re.escape(name) + r"\b", sentence):
            return name
    return None


def role_in_sentence(sentence, roles):
    """Participant whose role title is mentioned, else None."""
    low = sentence.lower()
    for role, name in roles.items():
        if role and role in low:
            return name
    return None


def resolve_owner(sentence, speaker, owner_map, fallback_to_speaker=True):
    """Owner resolution used by commitment rules.

    Order: explicit name mention -> role mention -> sentence-initial vocative
    -> speaker's own name (or 'Unassigned' when the caller disables the
    speaker fallback).
    """
    hit = name_in_sentence(sentence, owner_map["names"])
    if hit:
        return hit, "name-mention"
    hit = role_in_sentence(sentence, owner_map["roles"])
    if hit:
        return hit, "role-mention"
    hit = vocative(sentence)
    if hit:
        return hit, "vocative"
    spk = owner_map["speakers"].get(speaker)
    if spk and fallback_to_speaker:
        return spk["name"], "speaker"
    return "Unassigned", "unresolved"
