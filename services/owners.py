"""owners.py — per-meeting speaker -> real-name map from self-introductions.

The AMI teams introduce themselves at the start of early meetings
("I'm Laura and I'm the project manager"), so owners resolve to real names.
Falls back to "Unassigned" when no name can be determined.
"""
import re

# "I'm Laura and I'm the project manager" / "my name is David"
INTRO_RE = re.compile(
    r"\bI['\u2019]?m\s+([A-Z][a-zA-Z]{1,20})\b"
    r"(?:\s+and\s+I['\u2019]?m\s+(?:the\s+|our\s+|an?\s+)?([a-z][a-z ]{2,40}?))?"
    r"(?=[.,;!?]|$|\s)"
)
MY_NAME_RE = re.compile(r"\bmy name is\s+([A-Z][a-zA-Z]{1,20})\b", re.IGNORECASE)
I_AM_RE = re.compile(r"\bI am\s+([A-Z][a-zA-Z]{1,20})\b")

GENERIC_WORDS = {"Um", "Uh", "And", "So", "Well", "Yeah", "Okay", "Right", "Hi",
                 "Hello", "Sure", "Great", "Alright", "Mm", "Hmm", "Ah", "Oh"}


def build_map(turns):
    """Return {'speakers': {SPK-A: {'name':..,'role':..}}, 'names': [...],
    'roles': {role_string: name}} for one meeting."""
    speakers, names, roles = {}, [], {}
    for t in turns:
        spk = t["speaker"]
        if spk in speakers:
            continue
        name, role = None, None
        for m in INTRO_RE.finditer(t["text"]):
            cand = m.group(1)
            if cand in GENERIC_WORDS:
                continue
            name = cand
            if m.group(2):
                role = m.group(2).strip().lower()
            break
        if not name:
            m = MY_NAME_RE.search(t["text"]) or I_AM_RE.search(t["text"])
            if m and m.group(1) not in GENERIC_WORDS:
                name = m.group(1)
        if name:
            speakers[spk] = {"name": name, "role": role}
            names.append(name)
            if role:
                roles[role] = name
    return {"speakers": speakers, "names": names, "roles": roles}


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

    Order: explicit name mention -> role mention -> speaker's own name
    (or 'Unassigned' when the caller disables the speaker fallback).
    """
    hit = name_in_sentence(sentence, owner_map["names"])
    if hit:
        return hit, "name-mention"
    hit = role_in_sentence(sentence, owner_map["roles"])
    if hit:
        return hit, "role-mention"
    spk = owner_map["speakers"].get(speaker)
    if spk and fallback_to_speaker:
        return spk["name"], "speaker"
    return "Unassigned", "unresolved"
