# accompy.audio_renderers

Audio renderers — convert MidiData to AudioData.

Registered converters: MidiData -> AudioData

Backends:

- fluidsynth (via midi2audio): renders MIDI using SoundFont sample banks
- pretty_midi.fluidsynth: built-in FluidSynth integration in pretty_midi
- tonal.midi_to_wav: existing tonal package converter

Also provides end-to-end shortcuts: ChordSequence -> AudioData.

### Functions

| [`chordseq_to_audio_musicgen`](#accompy.audio_renderers.chordseq_to_audio_musicgen)(cs, \*[, prompt, ...])   | Generate audio directly from chords using MusicGen-Chord.             |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| [`midi_to_audio_dawdreamer`](#accompy.audio_renderers.midi_to_audio_dawdreamer)(md, \*[, vst_path, ...])   | Render MIDI to audio using DawDreamer with a VST plugin.              |
| [`midi_to_audio_fluidsynth`](#accompy.audio_renderers.midi_to_audio_fluidsynth)(md, \*[, soundfont, sr])   | Render MIDI to audio using FluidSynth CLI directly.                   |
| [`midi_to_audio_pretty_midi`](#accompy.audio_renderers.midi_to_audio_pretty_midi)(md, \*[, soundfont, sr])  | Render MIDI to audio using pretty_midi's built-in FluidSynth binding. |
| [`midi_to_audio_tonal`](#accompy.audio_renderers.midi_to_audio_tonal)(md, \*[, soundfont, sr])        | Render MIDI to audio using tonal.converters.midi_to_wav.              |

### accompy.audio_renderers.chordseq_to_audio_musicgen(cs, , prompt='smooth jazz trio', duration=None, sr=32000)

Generate audio directly from chords using MusicGen-Chord.

Uses Meta’s MusicGen model conditioned on chord progressions
to generate realistic audio without going through MIDI.

Requires: `pip install audiocraft` (or `pip install accompy[ai]`)

* **Parameters:**
  * **cs** ([`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)) – Chord progression to render
  * **prompt** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Text description of desired musical style
  * **duration** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – Duration in seconds. If None, computed from tempo and beats.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate (MusicGen default is 32000)
* **Return type:**
  [`AudioData`](accompy.converters.md#accompy.converters.AudioData)

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
>>> audio = chordseq_to_audio_musicgen(cs, prompt="jazz piano trio")
```

### accompy.audio_renderers.midi_to_audio_dawdreamer(md, , vst_path=None, sr=44100, duration=None, buffer_size=512)

Render MIDI to audio using DawDreamer with a VST plugin.

DawDreamer can host VST2/VST3 plugins for high-quality instrument sounds.
Falls back to a simple sine-wave synth if no VST is specified.

Requires: `pip install dawdreamer` (or `pip install accompy[vst]`)

* **Parameters:**
  * **md** ([`MidiData`](accompy.converters.md#accompy.converters.MidiData)) – MIDI data to render
  * **vst_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to a VST2/VST3 plugin (.so/.dylib/.dll/.vst3).
    If None, uses DawDreamer’s built-in synth.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
  * **duration** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – Duration in seconds. If None, computed from MIDI data.
  * **buffer_size** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio buffer size for rendering
* **Return type:**
  [`AudioData`](accompy.converters.md#accompy.converters.AudioData)

```pycon
>>> # md = MidiData(bytes_=some_midi_bytes)
>>> # audio = midi_to_audio_dawdreamer(md, vst_path="/path/to/plugin.vst3")
```

### accompy.audio_renderers.midi_to_audio_fluidsynth(md, , soundfont=None, sr=44100)

Render MIDI to audio using FluidSynth CLI directly.

Calls the `fluidsynth` binary via subprocess for maximum compatibility
across FluidSynth versions (midi2audio’s wrapper breaks on >=2.x).

Requires:

- FluidSynth installed (brew install fluidsynth / apt install fluidsynth)
- A SoundFont file (.sf2)

```pycon
>>> # md = MidiData(bytes_=some_midi_bytes)
>>> # audio = midi_to_audio_fluidsynth(md)
```

* **Return type:**
  [`AudioData`](accompy.converters.md#accompy.converters.AudioData)

### accompy.audio_renderers.midi_to_audio_pretty_midi(md, , soundfont=None, sr=44100)

Render MIDI to audio using pretty_midi’s built-in FluidSynth binding.

This calls pretty_midi’s .fluidsynth() method which uses pyfluidsynth.
Simpler setup than midi2audio but requires the FluidSynth C library.

* **Return type:**
  [`AudioData`](accompy.converters.md#accompy.converters.AudioData)

```pycon
>>> # md = MidiData(pretty_midi_obj=pm)
>>> # audio = midi_to_audio_pretty_midi(md)
```

### accompy.audio_renderers.midi_to_audio_tonal(md, , soundfont=None, sr=44100)

Render MIDI to audio using tonal.converters.midi_to_wav.

Uses the tonal package’s existing converter which wraps FluidSynth.

* **Return type:**
  [`AudioData`](accompy.converters.md#accompy.converters.AudioData)

```pycon
>>> # md = MidiData(bytes_=some_midi_bytes)
>>> # audio = midi_to_audio_tonal(md)
```
