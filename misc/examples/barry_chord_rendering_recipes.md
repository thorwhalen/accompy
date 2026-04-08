# Barry Chord Rendering Recipes

Code used to generate simple MIDI-to-WAV renderings of the Barry (6th diminished) chord sequence, and to batch-rename the resulting files. All code from a single conversation session.

## Context

The "Barry" sequence is a Barry Harris 6th-diminished scale harmonized as chords. In C:

```
C6 | Do | C6/E | Fo | C6/G | G#o | A- | Bo
```

It's an 8-bar pattern (typically repeated to make 16 bars). Each 6th chord alternates with a diminished chord a half-step above its bass note, creating a smooth chromatic ascending bass line.

---

## 1. Voicings for Eb (hand-crafted for smooth voice-leading)

The voicings were designed so that each chord shares 2-3 common tones with its neighbor, and remaining voices move by half-step. All voiced in the mid-piano range (Eb3-B4).

```python
VOICINGS_Eb = {
    # Eb6 root position: Eb3 G3 Bb3 C4
    "Eb6":     [51, 55, 58, 60],
    # Fo (F diminished): F3 Ab3 B3(Cb) D4
    "Fo":      [53, 56, 59, 62],
    # Eb6/G (1st inversion): G3 Bb3 C4 Eb4
    "Eb6/G":   [55, 58, 60, 63],
    # Abo (Ab diminished): Ab3 B3(Cb) D4 F4
    "Abo":     [56, 59, 62, 65],
    # Eb6/Bb (2nd inversion): Bb3 C4 Eb4 G4
    "Eb6/Bb":  [58, 60, 63, 67],
    # Bo (B diminished): B3 D4 F4 Ab4
    "Bo":      [59, 62, 65, 68],
    # C- (C minor): C4 Eb4 G4 Bb4
    "C-":      [60, 63, 67, 70],
    # Do (D diminished): D4 F4 Ab4 B4(Cb)
    "Do":      [62, 65, 68, 71],
}

PATTERN_Eb = ["Eb6", "Fo", "Eb6/G", "Abo", "Eb6/Bb", "Bo", "C-", "Do"]
```

### Transposition approach

To get voicings in another key, transpose all MIDI note numbers by the interval in semitones. For example, Eb to Ab = +5 semitones:

```python
TRANSPOSE = 5  # Eb -> Ab

VOICINGS_Ab = {
    "Ab6":     [51 + TRANSPOSE, 55 + TRANSPOSE, 58 + TRANSPOSE, 60 + TRANSPOSE],
    "Bbo":     [53 + TRANSPOSE, 56 + TRANSPOSE, 59 + TRANSPOSE, 62 + TRANSPOSE],
    "Ab6/C":   [55 + TRANSPOSE, 58 + TRANSPOSE, 60 + TRANSPOSE, 63 + TRANSPOSE],
    "Dbo":     [56 + TRANSPOSE, 59 + TRANSPOSE, 62 + TRANSPOSE, 65 + TRANSPOSE],
    "Ab6/Eb":  [58 + TRANSPOSE, 60 + TRANSPOSE, 63 + TRANSPOSE, 67 + TRANSPOSE],
    "Eo":      [59 + TRANSPOSE, 62 + TRANSPOSE, 65 + TRANSPOSE, 68 + TRANSPOSE],
    "F-":      [60 + TRANSPOSE, 63 + TRANSPOSE, 67 + TRANSPOSE, 70 + TRANSPOSE],
    "Go":      [62 + TRANSPOSE, 65 + TRANSPOSE, 68 + TRANSPOSE, 71 + TRANSPOSE],
}

# Or more concisely:
VOICINGS_Ab = {k: [p + TRANSPOSE for p in v] for k, v in VOICINGS_Eb_relabeled.items()}
```

---

## 2. Generate whole-note and quarter-note WAVs (full script)

This is the main script that was saved to `/tmp/barry_eb_chords.py` and run to produce two WAV files.

**What it does:**
- Defines hand-crafted voicings for the Barry sequence in Eb
- Builds two MIDI renderings using `pretty_midi`:
  - **Whole-note organ**: one chord strike per measure, sustained for the full measure (MIDI program 19 = Church Organ)
  - **Quarter-note piano**: chord restruck on every beat with downbeat accented (MIDI program 0 = Acoustic Piano)
- Renders audio using `pretty_midi.synthesize()` (built-in sine-wave synth, no FluidSynth needed)
- Writes 16-bit PCM WAV files via `scipy.io.wavfile`

**Key parameters:**
- Tempo: 100 BPM
- 5 passes through the 16-measure pattern = 80 measures total = ~3:12
- Velocity: 75 for whole notes; 80 on downbeats / 65 on other beats for quarter notes

```python
import pretty_midi
import numpy as np
import scipy.io.wavfile as wavfile

OUTPUT_DIR = "/Users/thorwhalen/Dropbox/_odata/music/my_ai_music_gen/barry_variations"

VOICINGS = {
    "Eb6":     [51, 55, 58, 60],
    "Fo":      [53, 56, 59, 62],
    "Eb6/G":   [55, 58, 60, 63],
    "Abo":     [56, 59, 62, 65],
    "Eb6/Bb":  [58, 60, 63, 67],
    "Bo":      [59, 62, 65, 68],
    "C-":      [60, 63, 67, 70],
    "Do":      [62, 65, 68, 71],
}

PATTERN = ["Eb6", "Fo", "Eb6/G", "Abo", "Eb6/Bb", "Bo", "C-", "Do"]

TEMPO = 100
BEATS_PER_MEASURE = 4
BEAT_DUR = 60.0 / TEMPO
MEASURE_DUR = BEATS_PER_MEASURE * BEAT_DUR
PASSES = 5
CHORDS = (PATTERN * 2) * PASSES  # 16 measures × 5 = 80 measures


def make_midi(chords, voicings, *, mode="whole", program=0, instrument_name="Piano"):
    """
    Build a PrettyMIDI object from a chord sequence.

    Parameters
    ----------
    chords : list[str]
        Sequence of chord names (keys into voicings dict), one per measure.
    voicings : dict[str, list[int]]
        Mapping from chord name to list of MIDI pitch numbers.
    mode : str
        "whole" = one chord per measure, sustained.
        "quarter" = chord restruck on every beat.
    program : int
        MIDI program number (0=Piano, 19=Church Organ, etc.)
    instrument_name : str
        Display name for the MIDI instrument.

    Returns
    -------
    pretty_midi.PrettyMIDI
    """
    pm = pretty_midi.PrettyMIDI(initial_tempo=TEMPO)
    inst = pretty_midi.Instrument(program=program, name=instrument_name)

    for i, chord_name in enumerate(chords):
        pitches = voicings[chord_name]
        measure_start = i * MEASURE_DUR

        if mode == "whole":
            start = measure_start
            end = measure_start + MEASURE_DUR - 0.02  # tiny gap to avoid overlap
            for p in pitches:
                inst.notes.append(
                    pretty_midi.Note(velocity=75, pitch=p, start=start, end=end)
                )
        elif mode == "quarter":
            for beat in range(BEATS_PER_MEASURE):
                start = measure_start + beat * BEAT_DUR
                end = start + BEAT_DUR - 0.02
                vel = 80 if beat == 0 else 65  # accent on downbeat
                for p in pitches:
                    inst.notes.append(
                        pretty_midi.Note(velocity=vel, pitch=p, start=start, end=end)
                    )

    pm.instruments.append(inst)
    return pm


def render_to_wav(pm, path, fs=44100):
    """
    Render a PrettyMIDI object to a 16-bit PCM WAV file.

    Uses pretty_midi's built-in synthesizer (sine waves).
    Normalizes to 90% peak to prevent clipping.
    """
    audio = pm.synthesize(fs=fs)
    peak = np.abs(audio).max()
    if peak > 0:
        audio = audio / peak * 0.9
    audio_16 = (audio * 32767).astype(np.int16)
    wavfile.write(path, fs, audio_16)
    print(f"Wrote: {path} ({len(audio_16) / fs:.1f}s, {len(audio_16) * 2:,} bytes)")


# Version 1: Whole-note organ
pm_whole = make_midi(CHORDS, VOICINGS, mode="whole", program=19, instrument_name="Organ")
render_to_wav(pm_whole, f"{OUTPUT_DIR}/barry_Eb_whole_organ.wav")

# Version 2: Quarter-note piano
pm_quarter = make_midi(CHORDS, VOICINGS, mode="quarter", program=0, instrument_name="Piano")
render_to_wav(pm_quarter, f"{OUTPUT_DIR}/barry_Eb_quarter_piano.wav")
```

---

## 3. Generate the Ab quarter-note piano variant

**What it does:** Takes the Eb voicings, transposes all pitches up 5 semitones to Ab, and generates the quarter-note piano rendering.

This was run as an inline script (not saved to a file).

```python
import pretty_midi
import numpy as np
import scipy.io.wavfile as wavfile

OUTPUT_DIR = "/Users/thorwhalen/Dropbox/_odata/music/my_ai_music_gen/barry_variations"

TRANSPOSE = 5  # Eb -> Ab

# Start from Eb voicings, relabeled for Ab, then transpose pitches
VOICINGS_EB_PITCHES = {
    "Ab6":     [51, 55, 58, 60],
    "Bbo":     [53, 56, 59, 62],
    "Ab6/C":   [55, 58, 60, 63],
    "Dbo":     [56, 59, 62, 65],
    "Ab6/Eb":  [58, 60, 63, 67],
    "Eo":      [59, 62, 65, 68],
    "F-":      [60, 63, 67, 70],
    "Go":      [62, 65, 68, 71],
}

VOICINGS = {k: [p + TRANSPOSE for p in v] for k, v in VOICINGS_EB_PITCHES.items()}

PATTERN = ["Ab6", "Bbo", "Ab6/C", "Dbo", "Ab6/Eb", "Eo", "F-", "Go"]

TEMPO = 100
BEATS_PER_MEASURE = 4
BEAT_DUR = 60.0 / TEMPO
MEASURE_DUR = BEATS_PER_MEASURE * BEAT_DUR
PASSES = 5
CHORDS = (PATTERN * 2) * PASSES

pm = pretty_midi.PrettyMIDI(initial_tempo=TEMPO)
inst = pretty_midi.Instrument(program=0, name="Piano")

for i, chord_name in enumerate(CHORDS):
    pitches = VOICINGS[chord_name]
    measure_start = i * MEASURE_DUR
    for beat in range(BEATS_PER_MEASURE):
        start = measure_start + beat * BEAT_DUR
        end = start + BEAT_DUR - 0.02
        vel = 80 if beat == 0 else 65
        for p in pitches:
            inst.notes.append(pretty_midi.Note(velocity=vel, pitch=p, start=start, end=end))

pm.instruments.append(inst)

audio = pm.synthesize(fs=44100)
peak = np.abs(audio).max()
if peak > 0:
    audio = audio / peak * 0.9
audio_16 = (audio * 32767).astype(np.int16)

path = f"{OUTPUT_DIR}/barry_Ab_quarter_piano.wav"
wavfile.write(path, 44100, audio_16)
print(f"Wrote: {path} ({len(audio_16)/44100:.1f}s)")
```

---

## 4. Batch rename: insert BPM into filenames

**What it does:** Renames all `.mp3` files in subdirectories of `barry_accompaniment_combos/`, inserting `_100bpm_` after the key portion of the filename.

Before: `barry_Eb_whole_organ__lofi-chill-hop__varA__aw0.45_sw0.75_02.mp3`
After: `barry_Eb_100bpm_whole_organ__lofi-chill-hop__varA__aw0.45_sw0.75_02.mp3`

**Pattern matched:** `barry_(Eb|Ab)_` -> `barry_(Eb|Ab)_100bpm_`

```bash
cd "/Users/thorwhalen/Dropbox/_odata/music/my_ai_music_gen/barry_variations/barry_accompaniment_combos"

find . -name '*.mp3' | while read f; do
  dir=$(dirname "$f")
  base=$(basename "$f")
  newbase=$(echo "$base" | sed -E 's/^(barry_(Eb|Ab))_/\1_100bpm_/')
  if [ "$base" != "$newbase" ]; then
    mv "$dir/$base" "$dir/$newbase"
  fi
done
```

This renamed 72 files across three subdirectories (`whole/`, `whole2/`, `quarter/`).

---

## Potential reusable tools

Functions/patterns that could be extracted into accompy or a utility module:

1. **`make_barry_voicings(key, *, base_octave=3)`** - Generate the 8 voice-led voicings for any key, given a base octave. Currently hand-crafted for Eb then transposed; could be computed from interval structure.

2. **`make_midi(chords, voicings, *, mode, tempo, program, ...)`** - Already well-factored. Takes a chord sequence + voicing dict and produces a `PrettyMIDI` object with either whole-note or quarter-note rendering.

3. **`render_to_wav(pm, path, *, fs=44100)`** - Renders `PrettyMIDI` to normalized 16-bit WAV. Simple wrapper around `pm.synthesize()` + `scipy.io.wavfile.write()`.

4. **`batch_rename_insert(directory, pattern, insertion, *, glob="*.mp3")`** - Generic batch rename utility that inserts a string at a regex-matched position in filenames.

### Dependencies

- `pretty_midi` (already an accompy dependency)
- `numpy`
- `scipy.io.wavfile`
