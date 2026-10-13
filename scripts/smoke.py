import sys, glob
sys.path.insert(0, '.')
from services import ingest, owners, extract, dates, risk
import datetime as dt

mids = ingest.meeting_ids()
missing = [m for m in mids
           if not glob.glob(f'data/ami-transcripts-speaker/{m}.*.transcript.txt')]
print('meetings:', len(mids), 'missing speaker files:', len(missing),
      missing[:5], flush=True)

mid = 'ES2002a'
turns = ingest.load_turns(mid)
omap = owners.build_map(turns)
print('speakers:', omap['speakers'], flush=True)
print('roles:', omap['roles'], flush=True)
items = extract.extract_meeting(mid, turns, omap,
                                dates.meeting_dates([mid])[mid])
print('items:', len(items), flush=True)
risk.apply(items, dt.date(2026, 10, 12))
for it in items[:10]:
    due = it['due']['date'] if it['due'] else '-'
    print('-', it['rule'], '|', it['owner'], '| due', due, '|',
          it['risk']['score'], it['risk']['tier'], '|', it['text'][:75],
          flush=True)
