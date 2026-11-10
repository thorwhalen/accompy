// accompy demo: chart -> note events (the package) -> a renderer (sound; demo code).
// The default renderer is the oscillator synth in ./oscillator.js. Another renderer module can be
// injected with ?renderer=<module URL>, same origin only: it exports createRenderer, with the
// contract documented in ./oscillator.js. The package itself produces events and leaves sound to the host.
import { beatsToSeconds, CHANNELS, generateEvents, STYLES } from "../dist/index.js";
import * as oscillator from "./oscillator.js";
import { prepareRenderer } from "./renderer_choice.js";
import { injectedRendererUrl } from "./renderer_url.js";

const $ = (id) => document.getElementById(id);
const chart = $("chart");
const style = $("style");
const tempo = $("tempo");
const repeats = $("repeats");
const play = $("play");
const status = $("status");

for (const name of STYLES) style.add(new Option(name, name, name === "swing", name === "swing"));

const PARTS = { [CHANNELS.drums]: "drums", [CHANNELS.bass]: "bass", [CHANNELS.piano]: "piano" };

/** @type {AudioContext | null} */
let ctx = null;
/** The renderer module: the oscillator synth, or the injected one once it has loaded. */
let rendererModule = Promise.resolve(oscillator);
/** Why the oscillator synth plays although another renderer was asked for; shown with every status. */
let notice = "";
try {
  const url = injectedRendererUrl();
  if (url) {
    rendererModule = import(url);
    rendererModule.catch(() => {}); // reported by prepareRenderer, which falls back
  }
} catch (error) {
  notice = ` (${error.message ?? error}; oscillator synth)`;
  status.textContent = notice.trim();
}
/** @type {Promise<{ renderer: { play: Function, allOff: Function }, notice: string }> | null} */
let prepared = null;
let endTimer = 0;
/** Bumped by every start and stop: a start that finds it changed after a wait was superseded. */
let runId = 0;

function stop() {
  runId++;
  void prepared?.then(({ renderer }) => renderer.allOff());
  clearTimeout(endTimer);
  if (status.textContent === "Loading sounds...") status.textContent = "";
  play.dataset.playing = "false";
  play.textContent = "Play";
}

async function start() {
  const run = ++runId;
  // Acknowledge the press at once, before any work.
  play.dataset.playing = "true";
  play.textContent = "Stop";
  status.className = "";
  let events;
  try {
    events = generateEvents(chart.value, { style: style.value, repeats: Number(repeats.value) || 1 });
  } catch (error) {
    stop();
    status.className = "error";
    status.textContent = String(error.message ?? error);
    return;
  }
  ctx ??= new AudioContext();
  void ctx.resume();
  if (!prepared) {
    status.textContent = "Loading sounds...";
    prepared = prepareRenderer(rendererModule, oscillator, ctx);
  }
  const { renderer: r, notice: why } = await prepared;
  if (run !== runId) return; // stopped (or restarted) while loading
  notice ||= why;
  const bpm = Math.min(300, Math.max(40, Number(tempo.value) || 120));
  const t0 = ctx.currentTime + 0.1;
  let end = 0;
  for (const e of events) {
    const at = t0 + beatsToSeconds(e.time, bpm);
    const seconds = beatsToSeconds(e.duration, bpm);
    end = Math.max(end, at + seconds);
    r.play(PARTS[e.channel] ?? "piano", e.note, e.velocity / 127, at, seconds);
  }
  status.textContent = `${events.length} note events, ${Math.round(end - t0)} s at ${bpm} BPM${notice}`;
  endTimer = setTimeout(stop, (end - ctx.currentTime + 0.2) * 1000);
}

play.addEventListener("click", () => {
  if (play.dataset.playing === "true") return stop();
  start().catch((error) => {
    stop();
    status.className = "error";
    status.textContent = String(error?.message ?? error);
  });
});
