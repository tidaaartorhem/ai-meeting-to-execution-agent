// Shared data shapes. Field names match the pipeline's JSON contract exactly.

export type Tier = "SAFE" | "WATCH" | "AT RISK" | "CRITICAL";

export type RuleName =
  | "action-marker"
  | "i-commitment"
  | "i-obligation"
  | "you-commitment"
  | "we-commitment"
  | "deadline-marker"
  | "need-to"
  | "third-commitment";

export interface DueInfo {
  raw: string;
  date: string; // YYYY-MM-DD
  kind: string;
}

export interface RiskInfo {
  score: number;
  tier: Tier;
  factors: string[];
}

export interface ExecItem {
  id: string;
  meeting: string;
  meeting_date: string;
  speaker: string;
  owner: string; // may be "Unassigned"
  text: string;
  quote: string;
  rule: string; // one of RuleName
  confidence: number;
  due: DueInfo | null;
  risk: RiskInfo;
}

export interface Meeting {
  id: string;
  meeting_date: string;
  turns: number;
  items: number;
  ownerless: number;
  dateless: number;
  overdue: number;
  avg_risk: number;
  top_risks: string[];
}

export interface OwnerStat {
  name: string;
  meetings: string[];
  open: number;
  overdue: number;
  no_due: number;
  overloaded: boolean;
}

export interface DigestRow {
  name: string;
  open: number;
  overdue: number;
  no_due: number;
  overloaded: boolean;
}

export interface OpenQuestion {
  id: string;
  text: string;
  owner: string;
  reason: string;
}

export interface Pulse {
  replay_today: string;
  meetings: number;
  items: number;
  overdue: number;
  ownerless: number;
  do_first: ExecItem[];
  owner_digest: DigestRow[];
  questions: OpenQuestion[];
}

export interface EvalData {
  n: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  note: string;
}

export function tierOf(score: number): Tier {
  if (score <= 29) return "SAFE";
  if (score <= 54) return "WATCH";
  if (score <= 79) return "AT RISK";
  return "CRITICAL";
}

export function isOverdue(item: ExecItem, replayToday: string): boolean {
  return item.due !== null && item.due.date < replayToday;
}
