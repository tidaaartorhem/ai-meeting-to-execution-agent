// Browser mirror of the pipeline's ordered extraction rules.
// Mirrors services/extract.py, services/dates.py, services/owners.py and
// services/risk.py: same rule order, same patterns, same confidences,
// same owner resolution, same due-date and risk logic. One deliberate
// difference: with no corpus-wide name lexicon, a "name mention" here is any
// capitalized non-stop word (the pipeline only accepts validated names).

import type { DueInfo, ExecItem, RiskInfo, RuleName, Tier } from "./types";
import { tierOf } from "./types";

interface RuleDef {
  name: RuleName;
  pattern: RegExp;
  confidence: number;
}

// Ordered rule list — first match wins. Exact mirror of RULES in
// services/extract.py, including confidences. Contractions are written out
// in full ("we'll", not "we'll?"): an optional apostrophe would match
// ordinary words ("Well", "hell").
export const RULES: RuleDef[] = [
  {
    name: "action-marker",
    pattern: /\baction\s*item\b|\baction\s*:|\btodo\b|\bto-?do\b|\bfollow[- ]up\b/i,
    confidence: 0.8,
  },
  {
    name: "i-commitment",
    pattern: /\bi'll\b|\bi will\b|\bi am going to\b|\bi'm gonna\b/i,
    confidence: 0.9,
  },
  {
    name: "i-obligation",
    pattern: /\bi have to\b|\bi need to\b/i,
    confidence: 0.7,
  },
  {
    name: "you-commitment",
    pattern:
      /\byou need to\b|\byou should\b|\byou have to\b|\byou must\b|\byou're going to\b|\byou're gonna\b|\bcan you\b|\bcould you\b|\bmake sure you\b|\bplease\b/i,
    confidence: 0.75,
  },
  {
    name: "we-commitment",
    pattern: /\bwe need to\b|\bwe should\b|\bwe have to\b|\bwe must\b|\bwe'll\b|\bwe will\b|\blet's\b/i,
    confidence: 0.65,
  },
  {
    name: "deadline-marker",
    pattern: /\bbefore the next meeting\b|\bby next time\b|\bfor next time\b|\bbefore we meet again\b/i,
    confidence: 0.7,
  },
  {
    name: "third-commitment",
    pattern: /\bhe'll\b|\bshe'll\b|\bhe will\b|\bshe will\b/i,
    confidence: 0.6,
  },
  { name: "need-to", pattern: /\bneeds? to\b/i, confidence: 0.6 },
];

// Rules whose owner falls back to the speaker when nobody is named;
// "you"/"we" commitments stay Unassigned without a name (same as pipeline).
const SPEAKER_FALLBACK: Record<RuleName, boolean> = {
  "action-marker": true,
  "i-commitment": true,
  "i-obligation": true,
  "you-commitment": false,
  "we-commitment": false,
  "deadline-marker": true,
  "third-commitment": true,
  "need-to": true,
};

const NAME_STOP = new Set([
  "I", "I'm", "I'll", "I've", "We", "We'll", "We've", "Let's",
  "You", "You'll", "He", "She", "It", "They", "The", "A", "An",
  "And", "But", "Or", "So", "If", "As", "At", "In", "On", "By", "To", "For",
  "Next", "This", "That", "These", "Those", "Today", "Tomorrow", "Yesterday",
  "Please", "Can", "Could", "Make", "Sure", "Do", "Does", "Will", "Monday",
  "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
  "Action", "Todo", "Follow", "Before", "After", "When", "What", "How",
  "Well", "Okay", "Yeah", "Yes", "Right", "Now",
]);

/** First capitalized word in the sentence that looks like a person's name. */
export function nameInSentence(text: string): string | null {
  const matches = text.match(/\b[A-Z][a-z]{2,}\b/g) ?? [];
  for (const m of matches) {
    if (!NAME_STOP.has(m)) return m;
  }
  return null;
}

const VOCATIVE_RE = /^([A-Z][a-z]{2,12}),\s+/;
const FILLER_LEAD =
  /^(?:(?:um|uh|er|ah|yes|mm-hmm?|yeah|yep|okay|ok|right|well|so|and|but|like|actually|anyway|alright|sure|great|hi|hello)[,.\s]+)+/i;

/** Sentence-initial addressed name ("David, can you ..."), or null. */
function vocative(sentence: string): string | null {
  const s = sentence.replace(FILLER_LEAD, "").trim();
  const m = s.match(VOCATIVE_RE);
  if (m && !NAME_STOP.has(m[1])) return m[1];
  return null;
}

function ownerForRule(rule: RuleName, text: string, speaker: string): string {
  const named = nameInSentence(text) ?? vocative(text);
  if (named) return named;
  if (SPEAKER_FALLBACK[rule]) return speaker;
  return "Unassigned";
}

/** Display text: strip leading filler words, collapse whitespace. */
function cleanText(sentence: string): string {
  return sentence.replace(FILLER_LEAD, "").trim().replace(/\s+/g, " ");
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function addDays(d: Date, n: number): Date {
  const c = new Date(d);
  c.setDate(c.getDate() + n);
  return c;
}

const WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

function nextWeekday(from: Date, name: string): Date {
  const target = WEEKDAYS.indexOf(name);
  let delta = (target - from.getDay() + 7) % 7;
  if (delta === 0) delta = 7;
  return addDays(from, delta);
}

/**
 * Parse a due date from a sentence. Mirrors services/dates.py: same pattern
 * order, same kinds ("next-meeting", "today", "tomorrow", "next-week",
 * "weeks-out", "end-of-week", "month-end", "weekday").
 */
export function parseDue(text: string, today: Date): DueInfo | null {
  const raw = (re: RegExp): string | null => {
    const m = text.match(re);
    return m ? m[0] : null;
  };
  let hit = raw(/\bbefore the next meeting\b|\bby next time\b|\bfor next time\b|\bbefore we meet again\b/i);
  if (hit) return { raw: hit, date: isoDate(addDays(today, 1)), kind: "next-meeting" };

  hit = raw(/\bin thirty minutes\b|\bin an hour\b|\bthis afternoon\b|\bby the end of the day\b|\btoday\b/i);
  if (hit) return { raw: hit, date: isoDate(today), kind: "today" };

  hit = raw(/\btomorrow\b/i);
  if (hit) return { raw: hit, date: isoDate(addDays(today, 1)), kind: "tomorrow" };

  hit = raw(/\bnext week\b/i);
  if (hit) return { raw: hit, date: isoDate(addDays(today, 7)), kind: "next-week" };

  hit = raw(/\bin (?:a|one) week\b/i);
  if (hit) return { raw: hit, date: isoDate(addDays(today, 7)), kind: "weeks-out" };

  hit = raw(/\bin two weeks\b|\bin a fortnight\b/i);
  if (hit) return { raw: hit, date: isoDate(addDays(today, 14)), kind: "weeks-out" };

  hit = raw(/\bby the end of the week\b/i);
  if (hit) return { raw: hit, date: isoDate(nextWeekday(today, "friday")), kind: "end-of-week" };

  hit = raw(/\bend of the month\b/i);
  if (hit) {
    const eom = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    return { raw: hit, date: isoDate(eom), kind: "month-end" };
  }

  hit = raw(/\b(?:by|on)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/i);
  if (hit) {
    const day = hit.match(/(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/i)![0].toLowerCase();
    return { raw: hit, date: isoDate(nextWeekday(today, day)), kind: "weekday" };
  }
  return null;
}

const VAGUE =
  ["think about", "look into", "sort out", "consider", "figure out", "maybe",
   "somehow", "at some point", "kind of", "sort of"];

/**
 * Deterministic risk scoring — mirrors services/risk.py. overloadCounts maps
 * an owner to their open-item count (for the "owner overloaded" +10); pass an
 * empty map to skip it. meetingDateISO enables the "stale" +10.
 */
export function scoreRisk(
  owner: string,
  text: string,
  due: DueInfo | null,
  todayISO: string,
  overloadCounts: Record<string, number> = {},
  meetingDateISO?: string,
): RiskInfo {
  let score = 0;
  const factors: string[] = [];
  if (owner === "Unassigned") {
    score += 35;
    factors.push("no owner");
  }
  if (due === null) {
    score += 25;
    factors.push("no due date");
  }
  const low = text.toLowerCase();
  if (VAGUE.some((v) => low.includes(v))) {
    score += 15;
    factors.push("vague verb");
  }
  if (due !== null && due.date < todayISO) {
    score += 30;
    factors.push("overdue");
  }
  if (owner !== "Unassigned" && (overloadCounts[owner] ?? 0) >= 4) {
    score += 10;
    factors.push("owner overloaded");
  }
  if (meetingDateISO) {
    const days = Math.round(
      (new Date(todayISO).getTime() - new Date(meetingDateISO).getTime()) / 86400000,
    );
    if (days > 5) {
      score += 10;
      factors.push("stale");
    }
  }
  score = Math.min(score, 100);
  return { score, tier: tierOf(score) as Tier, factors };
}

/** First ordered rule that fires for a sentence, or null. */
export function matchRule(text: string): RuleDef | null {
  for (const r of RULES) {
    if (r.pattern.test(text)) return r;
  }
  return null;
}

export interface ExtractOptions {
  today?: Date;
  meeting?: string;
  meetingDate?: string;
}

/**
 * Run extraction over pasted notes. Each blank-line-separated paragraph is a
 * turn; speakers rotate Speaker 1..5 and an "I'm <Name>" self-intro names that
 * speaker slot. Turns are split into sentences (like the pipeline) and the
 * first matching rule wins per sentence.
 */
export function extractFromTranscript(raw: string, opts: ExtractOptions = {}): ExecItem[] {
  const today = opts.today ?? new Date();
  const todayISO = isoDate(today);
  const meeting = opts.meeting ?? "paste";
  const meetingDate = opts.meetingDate ?? todayISO;

  const paragraphs = raw
    .split(/\n\s*\n/)
    .map((p) => p.replace(/\s+/g, " ").trim())
    .filter((p) => p.length > 0);

  const speakerNames = new Map<number, string>();
  const items: ExecItem[] = [];

  paragraphs.forEach((para, turnIdx) => {
    const slot = turnIdx % 5;
    const intro = para.match(/\bI'm ([A-Za-z]{2,20})\b/);
    if (intro && !speakerNames.has(slot) && !NAME_STOP.has(intro[1])) {
      speakerNames.set(slot, intro[1]);
    }
    const speaker = speakerNames.get(slot) ?? `Speaker ${slot + 1}`;

    const sentences = para.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
    sentences.forEach((sentence, sentIdx) => {
      if (sentence.split(/\s+/).length < 4) return;
      const rule = matchRule(sentence);
      if (!rule) return;
      const owner = ownerForRule(rule.name, sentence, speaker);
      const due = parseDue(sentence, today);
      items.push({
        id: `${meeting}-t${String(turnIdx).padStart(2, "0")}-s${String(sentIdx).padStart(2, "0")}`,
        meeting,
        meeting_date: meetingDate,
        speaker,
        owner,
        text: cleanText(sentence),
        quote: sentence.trim(),
        rule: rule.name,
        confidence: rule.confidence,
        due,
        risk: { score: 0, tier: "SAFE", factors: [] }, // scored below
      });
    });
  });

  // Second pass: owner-overload needs corpus-wide counts (here: the pasted set).
  const counts: Record<string, number> = {};
  for (const it of items) {
    if (it.owner !== "Unassigned") counts[it.owner] = (counts[it.owner] ?? 0) + 1;
  }
  for (const it of items) {
    it.risk = scoreRisk(it.owner, it.text, it.due, todayISO, counts, meetingDate);
  }
  return items.sort((a, b) => b.risk.score - a.risk.score);
}
