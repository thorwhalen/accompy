/**
 * Python semantics the twin needs where JavaScript differs: `str.strip`, `str.split()`,
 * `int(str)`, float `//`, `%` on negatives and `sum` of floats. Each is the smallest
 * exact copy of what CPython does on the inputs accompy passes.
 */
import { PY_WHITESPACE } from "./data.generated.js";

const WHITESPACE = new Set<number>(PY_WHITESPACE);

/** `ch` is whitespace for Python's `str.isspace` (JS `\s` differs: U+FEFF, U+001C-1F, U+0085). */
export function isPySpace(ch: string): boolean {
  return WHITESPACE.has(ch.codePointAt(0) ?? -1);
}

/** Python `s.strip()`: linear, never a regex (a JS trim regex is quadratic on long runs). */
export function pyStrip(s: string): string {
  let start = 0;
  let end = s.length;
  while (start < end && isPySpace(s[start]!)) start++;
  while (end > start && isPySpace(s[end - 1]!)) end--;
  return s.slice(start, end);
}

/** Python `s.split()` with no separator: runs of whitespace, no empty strings. */
export function pySplit(s: string): string[] {
  const out: string[] = [];
  let current = "";
  for (const ch of s) {
    if (isPySpace(ch)) {
      if (current) out.push(current);
      current = "";
    } else current += ch;
  }
  if (current) out.push(current);
  return out;
}

/** Python `int(s)` for a string: decimal, optional sign, `_` between digits; else RangeError. */
export function pyInt(s: string): number {
  const t = pyStrip(s);
  if (!/^[+-]?[0-9]+(_[0-9]+)*$/.test(t)) throw new RangeError(`invalid literal for int(): '${s}'`);
  return parseInt(t.replace(/_/g, ""), 10);
}

/** Python `a // b` on numbers (CPython's float floor division, exact for ints too). */
export function pyFloorDiv(a: number, b: number): number {
  if (b === 0) throw new RangeError("division by zero");
  if (Number.isInteger(a) && Number.isInteger(b)) return Math.floor(a / b);
  let mod = a % b;
  let div = (a - mod) / b;
  if (mod && b < 0 !== mod < 0) {
    mod += b;
    div -= 1;
  }
  if (!div) return 0;
  let floordiv = Math.floor(div);
  if (div - floordiv > 0.5) floordiv += 1;
  return floordiv;
}

/** Python `a % b` (the result takes the sign of `b`). */
export function pyMod(a: number, b: number): number {
  return ((a % b) + b) % b;
}

/** Python `int(x)` on a number: truncation toward zero. */
export function pyTrunc(x: number): number {
  return Math.trunc(x);
}

/**
 * Python (3.12+) `sum` of numbers: exact while the terms are integers, then
 * Neumaier-compensated, as CPython does for floats. Python 3.10/3.11 sum naively; the two
 * agree whenever the partial sums are exact (durations that are sums of powers of two).
 */
export function pySum(values: Iterable<number>): number {
  let f = 0;
  let c = 0;
  for (const x of values) {
    const t = f + x;
    if (Math.abs(f) >= Math.abs(x)) c += f - t + x;
    else c += x - t + f;
    f = t;
  }
  return c && Number.isFinite(c) ? f + c : f;
}
