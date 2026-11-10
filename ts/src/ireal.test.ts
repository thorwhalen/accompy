import { describe, expect, test } from "vitest";
import { parseIrealUrl } from "./ireal.js";

const PREFIX = "1r34LbKcu7";

describe("parseIrealUrl", () => {
  test("tier 1: irealb song, repeats flattened, time signature read, symbols kept as written", () => {
    const url = "irealb://Waltz=Roe%20Jane==Jazz%20Waltz=D-==" + PREFIX + "[T34D-7XyQKcl LZG7XyQ|C^7 Z==Jazz=120=1";
    expect(parseIrealUrl(url)).toEqual({
      measures: [["D-7"], ["D-7"], ["G7"], ["C^7"]],
      title: "Waltz",
      composer: "Roe Jane",
      key: "D-",
      timeSignature: [3, 4],
    });
  });

  test("tier 1: a playlist yields its first tune that parses", () => {
    const url = "irealb://Broken=Song===Second=C%20D==Bossa=G==" + PREFIX + "[C^7 A-7|D-7 G7 Z===My%20Playlist";
    const score = parseIrealUrl(url);
    expect(score.title).toBe("Second");
    expect(score.measures).toEqual([["C^7A-7"], ["D-7G7"]]);
  });

  test("tier 1: endings and an empty title", () => {
    const url = "irealb://=Anon==Swing=C==" + PREFIX + "{C^7XyQ|N1D-7 G7}XyQ|N2E-7 A7 Z";
    const score = parseIrealUrl(url);
    expect(score.title).toBe("Untitled");
    expect(score.measures).toEqual([["C^7"], ["D-7G7"], ["C^7"], ["E-7A7"]]);
  });

  test("tier 2: empty fields that make '===' inside one song", () => {
    const url = "irealb://Empty=Somebody===Swing=Bb==" + PREFIX + "[F7 |Bb7 Z=Jazz=120=2";
    expect(parseIrealUrl(url)).toMatchObject({ measures: [["F7"], ["Bb7"]], title: "Empty", key: "Bb" });
  });

  test("tier 3: unscrambled irealbook URL, symbols normalized", () => {
    const url = "irealbook://Old=Comp=Swing=G-=n=[C-7 |Bb^7 |Gm |Dm7 Z";
    expect(parseIrealUrl(url)).toEqual({
      measures: [["C-7"], ["Bb^7"], ["G-"], ["D-7"]],
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

  test("too few fields throws RangeError (Python ValueError)", () => {
    for (const url of ["", "irealb://", "hello", "irealbook://Song=Composer=Style"])
      expect(() => parseIrealUrl(url)).toThrow(RangeError);
  });
});
