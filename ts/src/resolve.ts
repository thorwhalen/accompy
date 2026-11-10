/**
 * Chord symbol -> MIDI notes, root first: the twin of `accompy.chord_resolution.tonal_resolver`.
 *
 * It reads the root and quality tables of Python's `tonal` package (generated into
 * `data.generated.ts`), with tonal's rules: the longest root name wins, case-insensitively
 * (Latin names such as `sol` and `sib` included); a slash bass is ignored; alterations
 * (`b9`, `#11`) and `addN` are dropped when the full quality is unknown. Notes are tonal's
 * (root near C4 = 60) moved by `transpose` (default -12, around C3 = 48).
 */
import { DEFAULT_TRANSPOSE, TONAL_CHORD_QUALITY, TONAL_ROOT_NOTES } from "./data.generated.js";
import { pyStrip } from "./py.js";

/** Chord symbol -> MIDI notes, root first. The renderer's chord-resolution seam. */
export type ChordResolver = (symbol: string) => number[];

const ROOTS = new Map<string, number>(TONAL_ROOT_NOTES as readonly (readonly [string, number])[]);
const QUALITIES = new Map<string, readonly number[]>(
  TONAL_CHORD_QUALITY as readonly (readonly [string, readonly number[]])[],
);
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// Stable sort, as Python's sorted(): equal lengths keep the table's order.
const ROOT_RE = new RegExp(
  `^(${[...ROOTS.keys()].sort((a, b) => b.length - a.length).map(escape).join("|")})`,
  "iu",
);

function parseRoot(chord: string): [string, number] {
  const match = ROOT_RE.exec(pyStrip(chord));
  if (!match) throw new RangeError(`Unknown root note in chord: '${chord}'`);
  const raw = match[1]!;
  if (ROOTS.has(raw)) return [raw, raw.length];
  const lower = raw.toLowerCase();
  if (ROOTS.has(lower)) return [lower, raw.length];
  for (const k of ROOTS.keys()) if (k.toLowerCase() === lower) return [k, raw.length];
  throw new RangeError(`Unknown root note: ${raw}`);
}

function simplifyQuality(qualityExtension: string): string {
  let qe = pyStrip(qualityExtension);
  if (!qe) return "";
  qe = qe.split("/")[0]!;
  if (QUALITIES.has(qe)) return qe;
  qe = qe.split("sus4").join("sus");
  // Python's \d matches any Unicode decimal digit.
  const qe2 = pyStrip(qe.replace(/[#b]\p{Nd}+/gu, "").replace(/add\p{Nd}+/gu, ""));
  return QUALITIES.has(qe2) ? qe2 : qe;
}

/** The MIDI notes of `symbol`, root first; throws RangeError for an unknown root or quality. */
export function tonalResolver(symbol: string, opts: { transpose?: number } = {}): number[] {
  const transpose = opts.transpose ?? DEFAULT_TRANSPOSE;
  const [root, rootLength] = parseRoot(symbol);
  const quality = simplifyQuality(pyStrip(symbol).slice(rootLength));
  const intervals = QUALITIES.get(quality);
  if (intervals === undefined) throw new RangeError(`Unknown quality/extension: ${quality}`);
  const rootMidi = ROOTS.get(root)!;
  return intervals.map((i) => rootMidi + i + (transpose ? transpose : 0));
}
