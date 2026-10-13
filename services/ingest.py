"""ingest.py — download (with local cache) and normalize AMI meeting transcripts.

Build-time discovery (documented in data/README-data.md): this mirror's
"merged" files are NOT chronological turns — each paragraph is one speaker's
entire concatenated contribution, byte-identical to the speaker-separated
files. The pipeline therefore uses the speaker-separated files directly:
each speaker's blob is split into segments (one segment per paragraph where
paragraph breaks exist; a single segment otherwise), labeled with the real
speaker key (SPK-A..D, occasionally SPK-E). Deterministic.
"""
import os
import re
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data", "ami-transcripts")
SPEAKER_DIR = os.path.join(REPO, "data", "ami-transcripts-speaker")
MIRROR = "https://raw.githubusercontent.com/gcunhase/AMICorpusXML/master/data/ami-transcripts"
SPEAKER_MIRROR = ("https://raw.githubusercontent.com/gcunhase/AMICorpusXML/master"
                  "/data/ami-transcripts-speaker")
FILE_LIST = os.path.join(REPO, "data", "file-list.txt")
SPEAKERS = ["A", "B", "C", "D", "E"]


def meeting_ids():
    with open(FILE_LIST) as f:
        return sorted(line.rsplit(".transcript.txt", 1)[0]
                      for line in f.read().split() if line.strip())


def download(meeting_id):
    """Fetch one merged transcript if not already cached (archival)."""
    path = os.path.join(DATA_DIR, f"{meeting_id}.transcript.txt")
    if os.path.exists(path):
        return path
    os.makedirs(DATA_DIR, exist_ok=True)
    urllib.request.urlretrieve(f"{MIRROR}/{meeting_id}.transcript.txt", path)
    return path


def speaker_path(meeting_id, speaker):
    return os.path.join(SPEAKER_DIR, f"{meeting_id}.{speaker}.transcript.txt")


def load_turns(meeting_id):
    """List of {'idx', 'speaker', 'text'} — one segment per speaker block.

    Cache-only: speaker files are fetched once at build time by
    fetch_all_speaker_files(). Missing speakers are skipped silently.
    """
    turns = []
    for spk in SPEAKERS:
        path = speaker_path(meeting_id, spk)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            blob = f.read()
        # Paragraph breaks where present; otherwise the whole blob is one turn.
        parts = [p.strip() for p in re.split(r"\n\s*\n|\n", blob) if p.strip()]
        for part in parts:
            text = re.sub(r"\s+", " ", part).strip()
            turns.append({"idx": len(turns), "speaker": f"SPK-{spk}",
                          "text": text})
    return turns


def load_all():
    """{meeting_id: [turns]} for all 171 meetings."""
    return {mid: load_turns(mid) for mid in meeting_ids()}
