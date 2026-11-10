// accompy demo: chart -> note events (the package) -> a minimal Web Audio synth (this file).
// The synth is demo-only: the package produces events and leaves sound to the host.
import { beatsToSeconds, CHANNELS, generateEvents, STYLES } from "../dist/index.js";

const $ = (id) => document.getElementById(id);
const chart = $("chart");
const style = $("style");
const tempo = $("tempo");
const repeats = $("repeats");
const play = $("play");
const status = $("status");

for (const name of STYLES) style.add(new Option(name, name, name === "swing", name === "swing"));

/** @type {AudioContext | null} */
let ctx = null;
/** @type {AudioScheduledSourceNode[]} */
let voices = [];
let endTimer = 0;

const midiToHz = (note) => 440 * 2 ** ((note - 69) / 12);

/** One enveloped oscillator note into `out`. */
function tone(out, { at, seconds, freq, type, gain, attack = 0.005, filter }) {
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, at);
  env.gain.setValueAtTime(0, at);
  env.gain.linearRampToValueAtTime(gain, at + attack);
  env.gain.exponentialRampToValueAtTime(0.0001, at + Math.max(seconds, attack + 0.02));
  let node = osc;
  if (filter) {
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = filter;
    osc.connect(lp);
    node = lp;
  }
  node.connect(env).connect(out);
  osc.start(at);
  osc.stop(at + seconds + 0.05);
  voices.push(osc);
}

let noiseBuffer = null;
function noise(out, { at, seconds, gain, highpass }) {
  noiseBuffer ??= (() => {
    const b = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return b;
  })();
  const src = ctx.createBufferSource();
  src.buffer = noiseBuffer;
  const hp = ctx.createBiquadFilter();
  hp.type = "highpass";
  hp.frequency.value = highpass;
  const env = ctx.createGain();
  env.gain.setValueAtTime(gain, at);
  env.gain.exponentialRampToValueAtTime(0.0001, at + seconds);
  src.connect(hp).connect(env).connect(out);
  src.start(at);
  src.stop(at + seconds + 0.05);
  voices.push(src);
}

/** General MIDI percussion, roughly: kick, snares, toms, then everything metallic as noise. */
function drum(out, note, at, v) {
  if (note === 35 || note === 36) {
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    osc.frequency.setValueAtTime(140, at);
    osc.frequency.exponentialRampToValueAtTime(45, at + 0.12);
    env.gain.setValueAtTime(v, at);
    env.gain.exponentialRampToValueAtTime(0.0001, at + 0.3);
    osc.connect(env).connect(out);
    osc.start(at);
    osc.stop(at + 0.35);
    voices.push(osc);
  } else if (note === 37) noise(out, { at, seconds: 0.04, gain: v * 0.6, highpass: 1800 });
  else if (note === 38 || note === 40) noise(out, { at, seconds: 0.16, gain: v * 0.7, highpass: 1200 });
  else if (note >= 41 && note <= 50 && ![42, 44, 46, 49].includes(note)) {
    tone(out, { at, seconds: 0.25, freq: midiToHz(note + 12), type: "sine", gain: v * 0.6 });
  } else {
    const long = note === 46 || note === 49 || note === 51 || note === 53;
    noise(out, { at, seconds: long ? 0.35 : 0.05, gain: v * 0.25, highpass: 7000 });
  }
}

function stop() {
  for (const v of voices) {
    try {
      v.stop();
    } catch {
      /* already stopped */
    }
  }
  voices = [];
  clearTimeout(endTimer);
  play.dataset.playing = "false";
  play.textContent = "Play";
}

function start() {
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
  const bpm = Math.min(300, Math.max(40, Number(tempo.value) || 120));
  const master = ctx.createGain();
  master.gain.value = 0.5;
  master.connect(ctx.destination);
  const t0 = ctx.currentTime + 0.1;
  let end = 0;
  for (const e of events) {
    const at = t0 + beatsToSeconds(e.time, bpm);
    const seconds = beatsToSeconds(e.duration, bpm);
    const v = e.velocity / 127;
    end = Math.max(end, at + seconds);
    if (e.channel === CHANNELS.drums) drum(master, e.note, at, v);
    else if (e.channel === CHANNELS.bass) {
      tone(master, { at, seconds, freq: midiToHz(e.note), type: "sawtooth", gain: v * 0.35, filter: 600 });
    } else tone(master, { at, seconds, freq: midiToHz(e.note), type: "triangle", gain: v * 0.12, attack: 0.01 });
  }
  status.textContent = `${events.length} note events, ${Math.round(end - t0)} s at ${bpm} BPM`;
  endTimer = setTimeout(stop, (end - ctx.currentTime + 0.2) * 1000);
}

play.addEventListener("click", () => (play.dataset.playing === "true" ? stop() : start()));
