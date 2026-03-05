# Tool Testing Notes

Notes from installing and testing various chord/MIDI/audio tools (March 2026).

## Working Tools

### pychord (v1.3.2)
- `pip install pychord` — installs cleanly
- API: `Chord("Cmaj7").components()` → `['C', 'E', 'G', 'B']`
- `Chord("Cmaj7").components_with_pitch(root_pitch=3)` → `['C3', 'E3', 'G3', 'B3']`
- Good coverage: major, minor, dim, aug, sus, 7th, 9th, 11th, 13th, altered
- No MIDI output directly — returns note names, needs conversion

### pretty_midi (v0.2.11)
- `pip install pretty_midi` — installs cleanly
- Very Pythonic API for building MIDI programmatically
- Built-in FluidSynth integration: `pm.fluidsynth(fs=44100)` → numpy array
- Requires `pyfluidsynth` for the `.fluidsynth()` method
- `note_name_to_number("C4")` → 60, `note_number_to_name(60)` → "C4"

### pyfluidsynth (v1.3.4)
- `pip install pyfluidsynth` — installs cleanly
- Required by pretty_midi's `.fluidsynth()` method
- Wraps the FluidSynth C library (needs `brew install fluidsynth`)
- Works well on macOS with Homebrew FluidSynth 2.5.2

### mido (v1.3.3)
- `pip install mido` — installs cleanly
- Lowest-level MIDI library — works with individual messages
- Good for custom MIDI file construction
- More verbose than pretty_midi but more control

### midiutil (v1.2.1)
- Already an accompy dependency
- Simple API: `MIDIFile(1)`, `addNote()`, `writeFile()`
- Less flexible than pretty_midi but simpler

### music21 (v9.9.1)
- `pip install music21` — large install but works
- Most comprehensive chord parser: handles `G7b9`, `Dm7b5`, Roman numerals
- `harmony.ChordSymbol("Cmaj7").pitches` → MIDI notes directly
- Can read MusicXML, MIDI, ABC, kern — universal hub
- Anchors chords around octave 3 (C3=48)

### mingus (v0.6.1)
- `pip install mingus` — installs cleanly
- Pure Python music theory library
- `chords.from_shorthand("Cm7")` → `['C', 'Eb', 'G', 'Bb']`
- `Note("C", 4)` → MIDI 48 (note: mingus octave 4 = MIDI 48, not 60!)
- Good for theory operations but MIDI note numbering differs from convention

### midi2audio (v0.1.1)
- `pip install midi2audio` — installs cleanly
- **ISSUE: Broken with FluidSynth >= 2.x** on macOS
- Passes CLI arguments in wrong order (`-F` after positional args)
- FluidSynth 2.x requires: `fluidsynth -F output.wav -r 44100 -ni soundfont.sf2 input.mid`
- Workaround: Use `subprocess.run()` directly with correct argument order

### tonal (existing dep)
- `chord_to_notes("Cmaj7")` → `[60, 64, 67, 71]` (anchored at C4=60)
- `midi_to_wav()` — wraps FluidSynth
- `chords_to_wav()` — full pipeline chord → MIDI → audio

## Failed Installs

### chords2midi
- `pip install chords2midi` — **FAILS**
- Build error: `FileNotFoundError: requirements.txt` not found in sdist
- Package appears unmaintained (broken build)
- Functionality is easily replicated with pychord + pretty_midi

## FluidSynth CLI Notes

FluidSynth 2.x (Homebrew) has strict argument ordering:
```bash
# CORRECT:
fluidsynth -F output.wav -r 44100 -ni soundfont.sf2 input.mid

# WRONG (what midi2audio does):
fluidsynth -ni soundfont.sf2 input.mid -F output.wav -r 44100
```

Options like `-F` and `-r` must come **before** the soundfont and MIDI file positional arguments.

## SoundFont Location
Default SoundFont on this system: `~/.fluidsynth/default_sound_font.sf2`

## Package Comparison: Chord Resolution

All 4 resolvers agree on pitch classes for common chords (tested across C, Am7, Dm7, G7).
Octave anchoring differs:
- **pychord**: configurable via `root_pitch` parameter (default octave 4)
- **music21**: anchors around octave 3 (C3=48 for major chords)
- **mingus**: octave 4 = MIDI 48 (different convention!)
- **tonal**: anchors at C4=60, we apply -12 transpose to get C3=48

All are normalized to octave 3 range in our resolvers for consistency.
