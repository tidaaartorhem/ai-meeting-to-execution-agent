"""ingest.py — download (with local cache) and normalize AMI meeting transcripts.

Deterministic: paragraphs = speaker turns, speakers labeled SPK-A..D by turn
order. The merged transcript files carry no speaker labels, so turn order is
the only signal.
"""
import os
import re
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data", "ami-transcripts")
MIRROR = "https://raw.githubusercontent.com/gcunhase/AMICorpusXML/master/data/ami-transcripts"
FILE_LIST = os.path.join(REPO, "data", "file-list.txt")


def meeting_ids():
    with open(FILE_LIST) as f:
        return sorted(line.rsplit(".transcript.txt", 1)[0]
                      for line in f.read().split() if line.strip())


def local_path(meeting_id):
    return os.path.join(DATA_DIR, f"{meeting_id}.transcript.txt")


def download(meeting_id):
    """Fetch one transcript if not already cached locally."""
    path = local_path(meeting_id)
    if os.path.exists(path):
        return path
    os.makedirs(DATA_DIR, exist_ok=True)
    url = f"{MIRROR}/{meeting_id}.transcript.txt"
    urllib.request.urlretrieve(url, path)
    return path


def load_turns(meeting_id):
    """Return list of {'idx', 'speaker', 'text'} for one meeting."""
    path = download(meeting_id)
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    # Paragraphs are separated by blank lines; each paragraph is one turn.
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    turns = []
    for i, p in enumerate(paras):
        text = re.sub(r"\s+", " ", p).strip()
        turns.append({"idx": i, "speaker": f"SPK-{chr(65 + (i % 4))}", "text": text})
    return turns


def load_all():
    """{meeting_id: [turns]} for all 171 meetings."""
    return {mid: load_turns(mid) for mid in meeting_ids()}
