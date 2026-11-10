// What the golden cases cannot pin: mutation (registries), injected seams, the helpers
// that copy Python semantics, and the guarantees the README makes.
import { describe, expect, it } from "vitest";
import {
  applySkeleton,
  beatsToSeconds,
  CHANNELS,
  chordEvents,
  generateEvents,
  listSkeletons,
  PatternRegistry,
  registerSkeleton,
  resolveSkeleton,
  RHYTHMIC_SKELETONS,
  STYLES,
  tonalResolver,
  type StylePatterns,
} from "./index.js";
import { pyFloorDiv, pyInt, pySplit, pyStrip, pySum } from "./py.js";

describe("generateEvents", () => {
  it("is deterministic and the same for every caller", () => {
    const chart = "| Dm7 G7 | C^7 | A7b9 |";
    for (const style of STYLES) expect(generateEvents(chart, { style })).toEqual(generateEvents(chart, { style }));
  });

  it("takes a chord resolver and a pattern source (the two seams)", () => {
    const resolver = () => [41, 45, 48];
    const events = generateEvents("| X | Y |", { style: "rock", chordResolver: resolver });
    expect(events.filter((e) => e.channel === CHANNELS.bass).every((e) => e.note % 12 === 5)).toBe(true);

    const only: StylePatterns = {
      drums: [{ name: "kick", beatsPerBar: 4, hits: [{ beat: 0, drum: 36, velocity: 100 }] }],
      bass: [],
      comp: [{ name: "stab", hits: [[2, 1, 100]] }],
    };
    const registry = new PatternRegistry({ builtins: false });
    registry.register("mine", only);
    const custom = generateEvents("| C |", { style: "mine", patternSource: registry, volumes: { drums: 1, piano: 1 } });
    expect(custom).toEqual([
      { time: 0, channel: 9, note: 36, velocity: 100, duration: 0.25 },
      { time: 2, channel: 1, note: 60, velocity: 100, duration: 1 },
      { time: 2, channel: 1, note: 64, velocity: 100, duration: 1 },
      { time: 2, channel: 1, note: 67, velocity: 100, duration: 1 },
    ]);
    expect(() => generateEvents("| C |", { style: "swing", patternSource: registry })).toThrow(RangeError);
  });

  it("is chordEvents applied chord by chord", () => {
    const whole = generateEvents("| C | Am |", { style: "bossa" });
    const byChord = [
      ...chordEvents(tonalResolver("C"), { style: "bossa", startBeat: 0 }),
      ...chordEvents(tonalResolver("A-"), { style: "bossa", startBeat: 4 }),
    ];
    expect(whole).toEqual(byChord);
  });
});

describe("registries", () => {
  it("a registry is independent of the shared one", () => {
    const registry = new PatternRegistry();
    expect(registry.styles()).toEqual([...STYLES]);
    expect(registry.unregister("swing")).toBe(true);
    expect(registry.styles()).not.toContain("swing");
    expect(new PatternRegistry().styles()).toContain("swing");
    expect(() => registry.register("bad", { drums: [] } as unknown as StylePatterns)).toThrow(RangeError);
  });

  it("registerSkeleton adds a skeleton every lookup sees", () => {
    registerSkeleton("test_groove", [1, 0.5, 0.5, 2], { name: "Test Groove", styles: ["test_style"] });
    try {
      expect(resolveSkeleton("test_groove")).toEqual([1, 0.5, 0.5, 2]);
      expect(resolveSkeleton("TEST GROOVE")).toEqual([1, 0.5, 0.5, 2]);
      expect(resolveSkeleton("test_style")).toEqual([1, 0.5, 0.5, 2]);
      expect(listSkeletons({ style: "test_style" })).toEqual(["test_groove"]);
      expect(RHYTHMIC_SKELETONS.get("test_groove")!.beatsPerMeasure).toBe(4);
      expect(applySkeleton([["C", 4]], "test_groove")).toEqual([["C", 1], ["C", 0.5], ["C", 0.5], ["C", 2]]);
    } finally {
      RHYTHMIC_SKELETONS.delete("test_groove");
    }
  });
});

describe("Python semantics", () => {
  it("strip and split use Python's whitespace, not JavaScript's", () => {
    expect(pyStrip("\u001c C \u0085")).toBe("C");
    expect(pyStrip("﻿C")).toBe("﻿C"); // U+FEFF: JS \s, not Python whitespace
    expect(pySplit(" C　Am\tF ")).toEqual(["C", "Am", "F"]);
  });

  it("strip is linear on long runs of whitespace", () => {
    const start = performance.now();
    expect(pyStrip("C" + " ".repeat(200_000) + "x")).toHaveLength(200_002);
    expect(performance.now() - start).toBeLessThan(1000);
  });

  it("int, floor division and sum behave as in CPython", () => {
    expect(pyInt(" 3 ")).toBe(3);
    expect(pyInt("1_0")).toBe(10);
    expect(() => pyInt("3.0")).toThrow(RangeError);
    expect(pyFloorDiv(-7, 2)).toBe(-4);
    expect(pyFloorDiv(4.5, 4)).toBe(1);
    expect(pyFloorDiv(0.3, 0.1)).toBe(2); // CPython: 0.3 // 0.1 == 2.0, while Math.floor(0.3 / 0.1) is 3
    expect(pySum([0.1, 0.2, 0.3])).toBe(0.6); // Python 3.12+: 0.6; a plain fold gives 0.6000000000000001
  });
});

describe("beatsToSeconds", () => {
  it("converts at any tempo; the events never depend on one", () => {
    expect(beatsToSeconds(4, 120)).toBe(2);
    expect(beatsToSeconds(1.5, 90)).toBe(1);
  });
});
