// The demo's default renderer: a tiny Web Audio oscillator synth, no samples to load.
// A renderer is what the demo plays note events into:
//   createRenderer({ context, destination }) -> { play(part, pitch, velocity, time, duration), allOff(), load?() }
// part is "drums" | "bass" | "piano"; velocity 0..1; time and duration in AudioContext seconds.
// Each note's end is scheduled with its start, so the renderer keeps no per-note state.

const midiToHz = (note) => 440 * 2 ** ((note - 69) / 12);

/** @param {{ context: BaseAudioContext, destination?: AudioNode }} options */
export function createRenderer({ context: ctx, destination = ctx.destination }) {
  const master = ctx.createGain();
  master.gain.value = 0.5;
  master.connect(destination);
  /** Sources started or scheduled, so allOff can cut them. */
  const sources = new Set();
  const track = (source) => {
    sources.add(source);
    source.onended = () => sources.delete(source);
  };

  /** One enveloped oscillator note. */
  function tone({ at, seconds, freq, type, gain, attack = 0.005, filter }) {
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
    node.connect(env).connect(master);
    osc.start(at);
    osc.stop(at + seconds + 0.05);
    track(osc);
  }

  let noiseBuffer = null;
  function noise({ at, seconds, gain, highpass }) {
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
    src.connect(hp).connect(env).connect(master);
    src.start(at);
    src.stop(at + seconds + 0.05);
    track(src);
  }

  /** General MIDI percussion, roughly: kick, snares, toms, then everything metallic as noise. */
  function drum(note, at, v) {
    if (note === 35 || note === 36) {
      const osc = ctx.createOscillator();
      const env = ctx.createGain();
      osc.frequency.setValueAtTime(140, at);
      osc.frequency.exponentialRampToValueAtTime(45, at + 0.12);
      env.gain.setValueAtTime(v, at);
      env.gain.exponentialRampToValueAtTime(0.0001, at + 0.3);
      osc.connect(env).connect(master);
      osc.start(at);
      osc.stop(at + 0.35);
      track(osc);
    } else if (note === 37) noise({ at, seconds: 0.04, gain: v * 0.6, highpass: 1800 });
    else if (note === 38 || note === 40) noise({ at, seconds: 0.16, gain: v * 0.7, highpass: 1200 });
    else if (note >= 41 && note <= 50 && ![42, 44, 46, 49].includes(note)) {
      tone({ at, seconds: 0.25, freq: midiToHz(note + 12), type: "sine", gain: v * 0.6 });
    } else {
      const long = note === 46 || note === 49 || note === 51 || note === 53;
      noise({ at, seconds: long ? 0.35 : 0.05, gain: v * 0.25, highpass: 7000 });
    }
  }

  return {
    play(part, pitch, velocity, time, duration) {
      if (part === "drums") drum(pitch, time, velocity);
      else if (part === "bass") {
        tone({ at: time, seconds: duration, freq: midiToHz(pitch), type: "sawtooth", gain: velocity * 0.35, filter: 600 });
      } else tone({ at: time, seconds: duration, freq: midiToHz(pitch), type: "triangle", gain: velocity * 0.12, attack: 0.01 });
    },
    allOff() {
      for (const source of sources) {
        try {
          source.stop();
        } catch {
          /* already stopped */
        }
      }
      sources.clear();
    },
  };
}
