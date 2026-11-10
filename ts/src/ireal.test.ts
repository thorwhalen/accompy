import { describe, expect, test } from "vitest";
import { parseIrealUrl } from "./ireal.js";
import { ValueError } from "./py.js";

const PREFIX = "1r34LbKcu7";
const song = (music: string, title = "T") => `irealb://${title}=X==Swing=C==${PREFIX}${music}=Jazz=120=1`;

describe("parseIrealUrl", () => {
  test("irealb song: repeat signs written out, time signature read, symbols kept as written", () => {
    const url = "irealb://Waltz=Roe%20Jane==Jazz%20Waltz=D-==" + PREFIX + "[T34D-7XyQKcl LZG7XyQ|C^7 Z==Jazz=120=1";
    expect(parseIrealUrl(url)).toEqual({
      measures: [["D-7"], ["D-7"], ["G7"], ["C^7"]],
      title: "Waltz",
      composer: "Roe Jane",
      key: "D-",
      timeSignature: [3, 4],
    });
  });

  test("a playlist yields its first tune with chords", () => {
    const url = "irealb://Broken=Song===Second=C%20D==Bossa=G==" + PREFIX + "[C^7 A-7|D-7 G7 Z===My%20Playlist";
    const score = parseIrealUrl(url);
    expect(score.title).toBe("Second");
    expect(score.measures).toEqual([["C^7", "A-7"], ["D-7", "G7"]]);
  });

  test("endings and an empty title", () => {
    const score = parseIrealUrl(song("{C^7XyQ|N1D-7 G7}XyQ|N2E-7 A7 Z", ""));
    expect(score.title).toBe("Untitled");
    expect(score.measures).toEqual([["C^7"], ["D-7", "G7"], ["C^7"], ["E-7", "A7"]]);
  });

  test("T12 is 12/8", () => {
    expect(parseIrealUrl(song("[T12C7 |F7 Z")).timeSignature).toEqual([12, 8]);
  });

  test("r repeats the previous two bars and keeps the next one", () => {
    expect(parseIrealUrl(song("[C |D |r| |E7 Z")).measures).toEqual([["C"], ["D"], ["C"], ["D"], ["E7"]]);
  });

  test("p with no chord before it is dropped; backslashes are literal", () => {
    expect(parseIrealUrl(song("[p C7|F7 p Z")).measures).toEqual([["C7"], ["F7", "F7"]]);
    expect(parseIrealUrl(song("{C7\\1D7 N1E7 }|N2F7 Z")).measures).toEqual([["C7\\1", "D7", "E7"], ["C7\\1", "D7"], ["F7"]]);
  });

  test("each bar is the list of its chords: spaces, commas, glued roots, p and W", () => {
    expect(parseIrealUrl(song("[C^7,A-7 D-7/FG7|p Bb7alt W/Ab Z")).measures).toEqual([
      ["C^7", "A-7", "D-7/F", "G7"],
      ["G7", "Bb7alt", "Bb7alt/Ab"],
    ]);
  });

  test("an empty composer shifts no field", () => {
    const url = "irealb://No%20Composer===Bossa=C-==" + PREFIX + "[C-7 |F7 Z=Latin=140=1";
    expect(parseIrealUrl(url)).toMatchObject({ title: "No Composer", composer: "", key: "C-" });
  });

  test("irealbook (plain) URL: bars as written, no normalization", () => {
    const url = "irealbook://Old=Comp=Swing=G-=n=[T44C-7 F7 |*AC^7 |Ah7 |Fo7 Z";
    expect(parseIrealUrl(url)).toEqual({
      measures: [["C-7", "F7"], ["C^7"], ["Ah7"], ["Fo7"]],
      title: "Old",
      composer: "Comp",
      key: "G-",
      timeSignature: [4, 4],
    });
  });

  test("lenient percent-decoding, as urllib.parse.unquote", () => {
    const score = parseIrealUrl("irealbook://Caf%C3%A9%ZZ=Bad%E9=S=K=n=C");
    expect(score.title).toBe("Café%ZZ");
    expect(score.composer).toBe("Bad�");
  });

  test("no chords throws ValueError", () => {
    for (const url of ["", "irealb://", "hello", "irealbook://Song=Composer=Style", song("Z ")])
      expect(() => parseIrealUrl(url)).toThrow(ValueError);
  });

  test("hostile charts decode in linear time (no nesting blow-up, no quadratic scans)", () => {
    const N = 40_000;
    const cases: Array<[string, number]> = [
      ["{".repeat(22) + "C " + "}".repeat(22), 2],
      ["{C }".repeat(N), 2 * N],
      ["<".repeat(N) + "C", 1],
      ["(".repeat(N) + "C", 1],
      ["{".repeat(N) + "C", 1],
      ["C }".repeat(N), 2 * N],
      ["{C |N1D }" + "|N2E".repeat(N), N + 3],
      ["C |r|".repeat(N), 3 * N - 2],
    ];
    for (const [chart, bars] of cases) {
      const start = performance.now();
      expect(parseIrealUrl(`irealbook://T=C=S=F=n=${chart}`).measures.length).toBe(bars);
      expect(performance.now() - start).toBeLessThan(5000);
    }
  });

  test("repeats keep their closing barline; endings, codas and quotes", () => {
    expect(parseIrealUrl(song("{C |D |N1E |F }N2G |A Z")).measures.flat()).toEqual("C D E F C D G A".split(" "));
    expect(parseIrealUrl(song("[G-7 |C7 Q|F^7 ]<D.C. al Coda>Q[Bb^7 Z")).measures.flat()).toEqual(
      "G-7 C7 F^7 G-7 C7 Bb^7".split(" "),
    );
    const url = `irealb://%22Round Midnight%22=Monk==Ballad=Eb-==${PREFIX}[Eb-^7 |Ab7 Z=Jazz=60=1"></a>`;
    expect(parseIrealUrl(url).title).toBe('"Round Midnight"');
  });
});
