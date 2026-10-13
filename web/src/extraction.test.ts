import { describe, expect, it } from "vitest";
import { extractFromTranscript, matchRule, parseDue, scoreRisk } from "./extraction";
import { tierOf } from "./types";

const TUESDAY = new Date(2026, 9, 13, 12, 0, 0); // 2026-10-13 (a Tuesday), local noon

describe("ordered extraction rules", () => {
  it("i-commitment: \"I'll send the slides\" assigns the speaker as owner", () => {
    const [item] = extractFromTranscript("I'll send the slides.");
    expect(item.rule).toBe("i-commitment");
    expect(item.owner).toBe("Speaker 1");
  });

  it("we-commitment: \"we need to finalize\" leaves the owner Unassigned", () => {
    const [item] = extractFromTranscript("We need to finalize the budget.");
    expect(item.rule).toBe("we-commitment");
    expect(item.owner).toBe("Unassigned");
  });

  it("you-commitment without a named person leaves the owner Unassigned", () => {
    const [item] = extractFromTranscript("You should update the docs.");
    expect(item.rule).toBe("you-commitment");
    expect(item.owner).toBe("Unassigned");
  });

  it("action-marker wins over i-commitment and picks the named owner", () => {
    const [item] = extractFromTranscript("Action item: David will draft the proposal.");
    expect(item.rule).toBe("action-marker");
    expect(item.owner).toBe("David");
  });

  it("self-intro name parsing: \"I'm Priya\" names that speaker slot", () => {
    // Turn 0 names slot 0; the same slot speaks again at turn 5.
    const notes = ["I'm Priya.", "Noted.", "Okay.", "Sure.", "Got it.", "I'll own this task now."].join(
      "\n\n",
    );
    const items = extractFromTranscript(notes);
    expect(items).toHaveLength(1);
    expect(items[0].speaker).toBe("Priya");
    expect(items[0].owner).toBe("Priya");
  });

  it("i-obligation: \"I have to\" / \"I need to\" assigns the speaker as owner", () => {
    const [item] = extractFromTranscript("I have to consult my legal advisor about it.");
    expect(item.rule).toBe("i-obligation");
    expect(item.owner).toBe("Speaker 1");
    expect(item.confidence).toBe(0.7);
  });

  it("matchRule returns null for plain chit-chat", () => {
    expect(matchRule("Great discussion today, thanks everyone.")).toBeNull();
  });

  it("does not match contractions against ordinary words (no optional apostrophe)", () => {
    // Regression: "we'll?" matched "Well"; "he'll?" matched "hell".
    expect(matchRule("Well, that wraps the agenda.")).toBeNull();
    expect(matchRule("What the hell is going on with the build?")).toBeNull();
    expect(matchRule("We'll finalize the budget.")).not.toBeNull();
    expect(matchRule("He'll follow up with the client.")).not.toBeNull();
    expect(matchRule("She will own the rollout.")).not.toBeNull();
  });
});

describe("due-date parsing", () => {
  it("parses \"by Friday\" to the next Friday from a Tuesday", () => {
    const due = parseDue("We need to finalize the budget by Friday.", TUESDAY);
    expect(due).not.toBeNull();
    expect(due!.date).toBe("2026-10-16");
    expect(due!.kind).toBe("weekday");
  });

  it("parses \"before the next meeting\" to tomorrow", () => {
    const due = parseDue("You'll finalize the spec before the next meeting.", TUESDAY);
    expect(due).not.toBeNull();
    expect(due!.date).toBe("2026-10-14");
    expect(due!.kind).toBe("next-meeting");
  });
});

describe("risk scoring", () => {
  it("ownerless + dateless item scores exactly 60", () => {
    const risk = scoreRisk("Unassigned", "we need to finalize the vendor shortlist", null, "2026-10-12");
    expect(risk.score).toBe(60);
    expect(risk.tier).toBe("AT RISK");
    expect(risk.factors).toEqual(["no owner", "no due date"]);
  });

  it("vague verbs add 15 and overdue adds 30", () => {
    const risk = scoreRisk(
      "David",
      "let's sort out the migration timeline somehow",
      { raw: "yesterday", date: "2026-10-12", kind: "relative" },
      "2026-10-13",
    );
    expect(risk.score).toBe(45); // 15 vague + 30 overdue
    expect(risk.tier).toBe("WATCH");
  });

  it("tier boundaries match the contract", () => {
    expect(tierOf(0)).toBe("SAFE");
    expect(tierOf(29)).toBe("SAFE");
    expect(tierOf(30)).toBe("WATCH");
    expect(tierOf(54)).toBe("WATCH");
    expect(tierOf(55)).toBe("AT RISK");
    expect(tierOf(79)).toBe("AT RISK");
    expect(tierOf(80)).toBe("CRITICAL");
    expect(tierOf(100)).toBe("CRITICAL");
  });
});
