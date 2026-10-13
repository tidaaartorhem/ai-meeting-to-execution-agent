import { useEffect, useState } from "react";
import type { EvalData, ExecItem, Meeting, OwnerStat, Pulse } from "./types";
import {
  fixtureEval,
  fixtureItems,
  fixtureMeetings,
  fixtureOwners,
  fixturePulse,
} from "./fixtures";
import QueueView from "./views/QueueView";
import RiskBoardView from "./views/RiskBoardView";
import MeetingsView from "./views/MeetingsView";
import PulseView from "./views/PulseView";
import PasteView from "./views/PasteView";
import "./styles.css";

const TABS = [
  { key: "queue", label: "Execution queue" },
  { key: "board", label: "Risk board" },
  { key: "meetings", label: "Meetings" },
  { key: "pulse", label: "Weekly pulse" },
  { key: "paste", label: "Paste-a-transcript" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

async function loadJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as T;
  } catch {
    return fallback; // render from fixtures with zero network
  }
}

interface DataState {
  items: ExecItem[];
  meetings: Meeting[];
  owners: OwnerStat[];
  pulse: Pulse;
  evalData: EvalData;
}

export default function App() {
  const [tab, setTab] = useState<TabKey>("queue");
  const [data, setData] = useState<DataState>({
    items: fixtureItems,
    meetings: fixtureMeetings,
    owners: fixtureOwners,
    pulse: fixturePulse,
    evalData: fixtureEval,
  });

  useEffect(() => {
    let live = true;
    Promise.all([
      loadJson<ExecItem[]>("items.json", fixtureItems),
      loadJson<Meeting[]>("meetings.json", fixtureMeetings),
      loadJson<OwnerStat[]>("owners.json", fixtureOwners),
      loadJson<Pulse>("pulse.json", fixturePulse),
      loadJson<EvalData>("eval.json", fixtureEval),
    ]).then(([items, meetings, owners, pulse, evalData]) => {
      if (live) setData({ items, meetings, owners, pulse, evalData });
    });
    return () => {
      live = false;
    };
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>Followthrough</h1>
        <p className="tagline">
          Meeting Execution Board — turns commitments made in meetings into a tracked, risk-ranked
          queue of who owes what by when.
        </p>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={tab === t.key ? "tab active" : "tab"}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="main">
        {tab === "queue" && <QueueView items={data.items} replayToday={data.pulse.replay_today} />}
        {tab === "board" && <RiskBoardView items={data.items} pulse={data.pulse} />}
        {tab === "meetings" && (
          <MeetingsView items={data.items} meetings={data.meetings} replayToday={data.pulse.replay_today} />
        )}
        {tab === "pulse" && <PulseView pulse={data.pulse} evalData={data.evalData} />}
        {tab === "paste" && <PasteView />}
      </main>
      <footer className="footer">
        Followthrough · deterministic extraction, deterministic risk scoring · data: {data.items.length}{" "}
        items across {data.meetings.length} meetings
      </footer>
    </div>
  );
}
