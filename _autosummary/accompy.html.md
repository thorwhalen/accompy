# accompy

accompy - Generate accompaniment audio from chord charts.

Generate backing tracks with bass, drums, piano from chord progressions,
similar to iReal Pro.

### Example

```pycon
>>> from accompy import generate_accompaniment, Score
>>>
>>> # Simple usage
>>> path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=120)
>>>
>>> # With Score object for more control
>>> score = Score.from_string("| Dm7 | G7 | C^7 | A7b9 |", title="ii-V-I")
>>> path = generate_accompaniment(score, style="swing", tempo=160, repeats=4)
```

Available styles: swing, bossa, rock, ballad, funk, latin, waltz, blues

Converter Pipeline:

```pycon
>>> from accompy import converter, ChordSequence, MidiData, convert
>>> # List available converters for a given step
>>> converter.list_converters(ChordSequence, MidiData)
>>> # Convert using the default or a named converter
>>> midi = convert(chord_seq, MidiData)
>>> midi = convert(chord_seq, MidiData, via="midiutil")
```

Advanced Usage (Extensibility):

```pycon
>>> # Register custom patterns
>>> from accompy import get_pattern_registry
>>> registry = get_pattern_registry()
>>> # registry['my_style'] = {'drums': [...], 'bass': [...], 'comp': [...]}
>>>
>>> # Use custom chord resolver
>>> from accompy import set_chord_resolver
>>> # set_chord_resolver(my_custom_resolver)
>>>
>>> # Access protocol definitions for custom implementations
>>> from accompy.protocols import ChordResolver, PatternSource, SynthesizerBackend
```

### Functions

| [`generate_accompaniment`](#accompy.generate_accompaniment)(chords, \*[, style, ...])   | Generate an accompaniment audio file from a chord progression.                                                 |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| [`ensure_score`](#accompy.ensure_score)(chords, \*[, title, key, ...])        | Coerce common chord-progression formats into a `Score`.                                                        |
| [`play_audio`](#accompy.play_audio)(audio_path)                             | Play an audio file using the system's default audio player.                                                    |
| [`check_dependencies`](#accompy.check_dependencies)()                               | Check which dependencies are available.                                                                        |
| [`print_setup_instructions`](#accompy.print_setup_instructions)()                         | Print installation instructions for missing dependencies.                                                      |
| [`convert`](#accompy.convert)(source, target_type, \*[, via])            | Convert source to target_type using the registered converter.                                                  |
| [`chords_to_sequence`](#accompy.chords_to_sequence)(chords, \*[, parser, ...])      | Parse a chord string into a ChordSequence.                                                                     |
| [`chords_to_notes`](#accompy.chords_to_notes)(chords, \*[, resolver, tempo])     | Convert chord string or ChordSequence to resolved MIDI notes.                                                  |
| [`chords_to_midi`](#accompy.chords_to_midi)(chords, \*[, resolver, ...])        | Convert chord string to MIDI data.                                                                             |
| [`chords_to_audio`](#accompy.chords_to_audio)(chords, \*[, resolver, ...])       | Convert chord string to audio.                                                                                 |
| [`midi_to_audio`](#accompy.midi_to_audio)(midi_data, \*[, ...])                | Convert MidiData to audio.                                                                                     |
| [`file_to_audio`](#accompy.file_to_audio)(filepath, \*[, output_path, ...])    | Convert an iReal Pro HTML/URL file to audio.                                                                   |
| [`file_to_midi`](#accompy.file_to_midi)(filepath, \*[, output_path, ...])     | Convert an iReal Pro HTML/URL file to MIDI.                                                                    |
| [`list_available_converters`](#accompy.list_available_converters)()                        | List all available converters organized by pipeline stage.                                                     |
| [`rhythm_to_midi`](#accompy.rhythm_to_midi)(chords, \*[, skeleton, ...])        | Convert chords to MIDI using a rhythmic skeleton for restrike timing.                                          |
| [`rhythm_to_audio`](#accompy.rhythm_to_audio)(chords, \*[, skeleton, ...])       | Convert chords to audio using a rhythmic skeleton for restrike timing.                                         |
| [`resolve_skeleton`](#accompy.resolve_skeleton)(skeleton)                         | Resolve a skeleton specification to a tuple of durations.                                                      |
| [`apply_skeleton`](#accompy.apply_skeleton)(cs, skeleton)                       | Apply a rhythmic skeleton to a chord sequence.                                                                 |
| [`register_skeleton`](#accompy.register_skeleton)(key, pattern, \*[, name, ...])   | Register a custom rhythmic skeleton.                                                                           |
| [`list_skeletons`](#accompy.list_skeletons)(\*[, beats_per_measure, style])     | List available skeleton keys, optionally filtered.                                                             |
| [`parse_ireal_html`](#accompy.parse_ireal_html)(html_path)                        | Extract a Score from an iReal Pro HTML export file.                                                            |
| [`parse_ireal_url`](#accompy.parse_ireal_url)(url)                               | Parse an iReal Pro URL into a Score object.                                                                    |
| [`transpose_score`](#accompy.transpose_score)(score, target_key)                 | Transpose a [`Score`](#accompy.Score) to a new key.                               |
| [`transpose_chord`](#accompy.transpose_chord)(chord, semitones, \*[, use_flat])  | Transpose a chord symbol by *semitones*.                                                                       |
| [`transpose_note`](#accompy.transpose_note)(name, semitones, \*[, use_flat])    | Transpose a single note name by *semitones*.                                                                   |
| [`generate_wav`](#accompy.generate_wav)(score, output_path, \*[, ...])        | Generate a WAV file from a Score using a pluggable engine.                                                     |
| [`generate_mma_wav`](#accompy.generate_mma_wav)(score, output_path, \*[, ...])    | Alias for [`mma_score_to_wav()`](#accompy.mma_score_to_wav).                                 |
| [`mma_score_to_wav`](#accompy.mma_score_to_wav)(score, output_path, \*[, ...])    | Render a Score to WAV using MMA (Musical MIDI Accompaniment).                                                  |
| [`make_converter_engine`](#accompy.make_converter_engine)(\*[, resolver, ...])         | Create a [`ScoreToWav`](#accompy.ScoreToWav) engine from accompy's converter pipeline. |
| [`generate_variations`](#accompy.generate_variations)(score, output_dir, \*[, ...])  | Batch-generate WAV files for many key / tempo / groove combinations.                                           |
| [`render_chords`](#accompy.render_chords)(chords, \*[, ...])                   | Render chords to a high-quality audio file, optionally AI-enhanced.                                            |
| [`render_chords_batch`](#accompy.render_chords_batch)(configs, \*\*shared_kwargs)    | Run [`render_chords()`](#accompy.render_chords) for each config dict.                     |
| [`get_patterns`](#accompy.get_patterns)(style)                                | Get all patterns for a given style.                                                                            |
| [`get_pattern_registry`](#accompy.get_pattern_registry)()                             | Get the global pattern registry, initializing if needed.                                                       |
| [`register_style`](#accompy.register_style)(style, drums, bass, comp)           | Register a custom style with the global registry.                                                              |
| [`verify_and_setup`](#accompy.verify_and_setup)([interactive, auto_fix])          | Verify all dependencies and optionally auto-configure.                                                         |
| [`setup_soundfont`](#accompy.setup_soundfont)([force])                           | Download and configure a SoundFont file.                                                                       |
| [`diagnose_issues`](#accompy.diagnose_issues)()                                  | Diagnose common setup issues and provide solutions.                                                            |
| [`print_diagnostic_report`](#accompy.print_diagnostic_report)()                          | Print a comprehensive diagnostic report.                                                                       |
| [`chord_to_notes`](#accompy.chord_to_notes)(symbol)                             | Convert chord symbol to MIDI notes using the current default resolver.                                         |
| [`get_chord_resolver`](#accompy.get_chord_resolver)()                               | Get the current default chord resolver.                                                                        |
| [`set_chord_resolver`](#accompy.set_chord_resolver)(resolver)                       | Set the default chord resolver.                                                                                |
| [`tonal_resolver`](#accompy.tonal_resolver)(symbol, \*[, transpose])            | Resolve chord symbol to MIDI notes using the tonal package (default).                                          |
| [`get_app_folder`](#accompy.get_app_folder)(\*[, folder_kind])                  | Return the app directory for *folder_kind*, creating it if needed.                                             |
| [`get_resource`](#accompy.get_resource)(name)                                 | Return a user resource path, seeding from package data if missing.                                             |
| [`get_config`](#accompy.get_config)(name)                                   | Return a config file path, seeding from package data if missing.                                               |
| [`get_artifact_dir`](#accompy.get_artifact_dir)(kind)                             | Return (and create) an artifact sub-directory for *kind*.                                                      |
| [`load_resource_text`](#accompy.load_resource_text)(name)                           | Read a resource file as text.                                                                                  |
| [`load_resource_lines`](#accompy.load_resource_lines)(name)                          | Read a resource file as a list of non-empty stripped lines.                                                    |
| [`load_resource_json`](#accompy.load_resource_json)(name)                           | Read a resource file as JSON.                                                                                  |

### Classes

| [`Score`](#accompy.Score)(measures[, title, composer, key, ...])      | A musical score containing chord events and metadata.                                         |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`ChordEvent`](#accompy.ChordEvent)(symbol[, beats])                       | A chord at a specific position in the progression.                                            |
| [`AccompanimentConfig`](#accompy.AccompanimentConfig)([style, tempo, repeats, ...]) | Configuration for accompaniment generation.                                                   |
| [`MidiEvent`](#accompy.MidiEvent)(time, channel, note, velocity, ...)     | A single MIDI event.                                                                          |
| [`ChordSequence`](#accompy.ChordSequence)(chords[, title, key, tempo, ...])   | Ordered sequence of (chord_symbol, duration_beats) pairs with metadata.                       |
| [`NoteSequence`](#accompy.NoteSequence)(notes[, tempo, time_signature])      | Ordered sequence of (midi_notes, duration_beats) with metadata.                               |
| [`MidiData`](#accompy.MidiData)([bytes_, pretty_midi_obj, tempo, ...])   | Container for MIDI data — either as bytes or as a pretty_midi object.                         |
| [`AudioData`](#accompy.AudioData)(waveform[, sr])                         | Container for audio data — numpy array + sample rate.                                         |
| [`ConverterRegistry`](#accompy.ConverterRegistry)()                               | Registry mapping (source_type, target_type) to named converter functions.                     |
| [`ScoreToWav`](#accompy.ScoreToWav)(\*args, \*\*kwargs)                    | Callable that renders a [`Score`](#accompy.Score) to a WAV file. |
| [`DrumPattern`](#accompy.DrumPattern)(name, beats_per_bar, hits)            | A drum pattern for one or more measures.                                                      |
| [`BassPattern`](#accompy.BassPattern)(name, notes)                          | A bass pattern template.                                                                      |
| [`CompingPattern`](#accompy.CompingPattern)(name, hits)                        | A piano/guitar comping (accompaniment) pattern.                                               |
| [`DrumHit`](#accompy.DrumHit)(beat, drum, velocity)                     | A single drum hit in a pattern.                                                               |
| [`NoteEvent`](#accompy.NoteEvent)(beat, pitch_offset, duration, velocity) | A melodic note event for bass or other instruments.                                           |
| [`ChordResolver`](#accompy.ChordResolver)(\*args, \*\*kwargs)                 | Convert chord symbols to MIDI note numbers.                                                   |
| [`PatternSource`](#accompy.PatternSource)(\*args, \*\*kwargs)                 | Provides musical patterns for a given style.                                                  |
| [`SynthesizerBackend`](#accompy.SynthesizerBackend)(\*args, \*\*kwargs)            | Audio synthesis backend.                                                                      |
| [`RealtimeAccompaniment`](#accompy.RealtimeAccompaniment)([config, on_event])         | Real-time accompaniment player (foundation for future work).                                  |

### *class* accompy.AccompanimentConfig(style='swing', tempo=120, repeats=2, instruments=<factory>, volumes=<factory>, soundfont=None, sample_rate=44100, output_format='wav', chord_resolver=None, pattern_source=None, synthesis_backend=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for accompaniment generation.

This is the single source of truth for all configuration options,
including dependency injection hooks for extensibility.

#### style

Musical style (swing, bossa, rock, etc.)

#### tempo

Beats per minute

#### repeats

Number of times to play through the form

#### instruments

Which instruments to include

#### volumes

Relative volume for each instrument (0.0-1.0)

#### soundfont

Path to SoundFont file for synthesis

#### sample_rate

Audio sample rate

#### output_format

Output file format

#### chord_resolver

Optional custom chord resolution function

#### pattern_source

Optional custom pattern provider

#### synthesis_backend

Optional custom synthesis backend

#### with_overrides(\*\*kwargs)

Create a new config with specified overrides.

This enables immutable updates to configuration.

* **Return type:**
  [`AccompanimentConfig`](accompy.base.html.md#accompy.base.AccompanimentConfig)

### Example

```pycon
>>> config = AccompanimentConfig(tempo=120)
>>> fast_config = config.with_overrides(tempo=180)
>>> config.tempo, fast_config.tempo
(120, 180)
```

### *class* accompy.AudioData(waveform, sr=44100)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Container for audio data — numpy array + sample rate.

```pycon
>>> import numpy as np
>>> ad = AudioData(waveform=np.zeros(44100), sr=44100)
>>> ad.duration_seconds
1.0
```

#### to_wav_bytes()

Convert to WAV file bytes.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

#### write(path)

Write audio to a WAV file. Returns the path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* accompy.BassPattern(name, notes)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A bass pattern template.

Uses pitch_offset in NoteEvent to specify intervals from the chord root.
The actual pitches are determined when the pattern is applied to specific chords.

### *class* accompy.ChordEvent(symbol, beats=4)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A chord at a specific position in the progression.

### Example

```pycon
>>> event = ChordEvent("Dm7", beats=4)
>>> event.symbol
'D-7'
```

### *class* accompy.ChordResolver(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Convert chord symbols to MIDI note numbers.

Example implementation:

```pycon
>>> def my_resolver(symbol: str) -> list[int]:
...     # Return MIDI notes for chord
...     return [60, 64, 67]  # C major
```

### *class* accompy.ChordSequence(chords, title='', key='C', tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Ordered sequence of (chord_symbol, duration_beats) pairs with metadata.

This is the canonical internal representation of a chord progression.

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 8.0)])
>>> len(cs)
3
>>> cs[0]
('Dm7', 4.0)
>>> cs.total_beats
16.0
```

#### *property* durations *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[float](https://docs.python.org/3/builtins/functions.html#float)]*

Just the durations, without symbols.

#### *property* symbols *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

Just the chord symbols, without durations.

#### to_score()

Convert to an accompy Score for pattern-based accompaniment.

### Example

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
>>> score = cs.to_score()
>>> len(score)
2
```

### *class* accompy.CompingPattern(name, hits)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A piano/guitar comping (accompaniment) pattern.

#### name

Pattern identifier

#### hits

Sequence of (beat, duration, velocity) tuples

### *class* accompy.ConverterRegistry

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Registry mapping (source_type, target_type) to named converter functions.

Supports multiple converters for the same type pair, distinguished by name.
The first registered converter becomes the default.

```pycon
>>> reg = ConverterRegistry()
>>> reg.register(str, int, int, name='builtin')
>>> reg[str, int]('42')
42
>>> reg.list_converters(str, int)
['builtin']
```

#### get(source_type, target_type, name=None)

Get a specific named converter, or the default if name is None.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)

#### list_converters(source_type, target_type)

List available converter names for a type pair.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### list_pairs()

List all registered (source, target) type name pairs.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

#### register(source_type, target_type, func, , name='', is_default=False)

Register a converter function.

* **Parameters:**
  * **source_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The input type
  * **target_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The output type
  * **func** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)) – The converter function (source -> target)
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name for this converter (defaults to func._\_name_\_)
  * **is_default** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, make this the default converter for this pair
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### set_default(source_type, target_type, name)

Change the default converter for a type pair.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* accompy.DrumHit(beat, drum, velocity)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single drum hit in a pattern.

#### beat

Beat position (0-based within measure)

#### drum

MIDI note number for the drum sound

#### velocity

Hit velocity (0-127)

### *class* accompy.DrumPattern(name, beats_per_bar, hits)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A drum pattern for one or more measures.

### Example

```pycon
>>> pattern = DrumPattern("rock", 4, [DrumHit(0, KICK, 100)])
>>> pattern.beats_per_bar
4
```

#### at_tempo(tempo)

Return pattern duration in seconds at a given tempo.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### *class* accompy.MidiData(bytes_=None, pretty_midi_obj=None, tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Container for MIDI data — either as bytes or as a pretty_midi object.

Wraps MIDI content so converters have a uniform interface regardless
of which MIDI library produced the data.

```pycon
>>> import io
>>> md = MidiData(bytes_=b'MThd...', tempo=120)
>>> md.has_bytes
True
```

#### to_bytes()

Get MIDI as bytes, converting from pretty_midi if needed.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

#### to_pretty_midi()

Get as pretty_midi.PrettyMIDI, converting from bytes if needed.

#### write(path)

Write MIDI to a file. Returns the path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* accompy.MidiEvent(time, channel, note, velocity, duration)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single MIDI event.

Used for event-based MIDI generation that enables both batch file creation
and future real-time streaming.

#### time

Event time in beats

#### channel

MIDI channel (0-15)

#### note

MIDI note number (0-127)

#### velocity

Note velocity (0-127)

#### duration

Note duration in beats

### *class* accompy.NoteEvent(beat, pitch_offset, duration, velocity)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A melodic note event for bass or other instruments.

#### beat

Beat position within measure

#### pitch_offset

Offset from chord root in semitones (0=root, 7=5th, etc.)

#### duration

Note duration in beats

#### velocity

Note velocity (0-127)

### *class* accompy.NoteSequence(notes, tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Ordered sequence of (midi_notes, duration_beats) with metadata.

Represents resolved chords — chord symbols have been converted to
concrete MIDI note numbers.

```pycon
>>> ns = NoteSequence([([60, 64, 67], 4.0), ([62, 65, 69], 4.0)])
>>> ns[0]
([60, 64, 67], 4.0)
```

### *class* accompy.PatternSource(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Provides musical patterns for a given style.

### Example

```pycon
>>> class MyPatternSource:
...     def get_patterns(self, style: str) -> dict:
...         return {'drums': [...], 'bass': [...], 'comp': [...]}
...     def available_styles(self) -> list[str]:
...         return ['swing', 'bossa']
```

#### available_styles()

List all available style names.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of style names

#### get_patterns(style)

Get patterns for a style.

* **Parameters:**
  **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Style name (e.g., “swing”, “bossa”, “rock”)
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)]
* **Returns:**
  Dict with ‘drums’, ‘bass’, ‘comp’ keys containing pattern lists

### *class* accompy.RealtimeAccompaniment(config=None, , on_event=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Real-time accompaniment player (foundation for future work).

This class separates event scheduling from synthesis, enabling integration
with real-time audio systems. Current implementation generates events;
future versions will integrate with hum/pyo for actual audio synthesis.

Example (current usage):

```pycon
>>> from accompy import AccompanimentConfig
>>> config = AccompanimentConfig(tempo=120, style='swing')
>>> player = RealtimeAccompaniment(config)
>>> player.set_chords([('Dm7', 4), ('G7', 4), ('Cmaj7', 8)])
>>> events_iter = player.events()  # Get event iterator
>>> # Future: for event in events_iter: synth.play(event.note, event.velocity)
```

Future usage (with hum integration):

```pycon
>>> from hum.pyo_util import Synth
>>> def on_event(event: MidiEvent):
...     # Send MIDI event to synth in real-time
...     synth.send_note(event.note, event.velocity, event.duration)
>>> player = RealtimeAccompaniment(config, on_event=on_event)
>>> player.play()
```

#### events()

Generate events for current chord progression.

* **Yields:**
  MidiEvent objects in chronological order
* **Return type:**
  [*Iterator*](https://docs.python.org/3/library/typing.html#typing.Iterator)[[*MidiEvent*](accompy.base.html.md#accompy.base.MidiEvent)]

### Example

```pycon
>>> player = RealtimeAccompaniment()
>>> player.set_chords([('C', 4)])
>>> events = list(player.events())
>>> len(events) > 0
True
```

#### play()

Play the accompaniment (future implementation).

This will integrate with a real-time synthesis backend (hum/pyo)
to actually play audio. Current implementation is a placeholder.

* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/builtins/exceptions.html#NotImplementedError) – Real-time playback not yet implemented
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### set_chords(chords)

Update the chord progression.

* **Parameters:**
  **chords** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Chord progression in any supported format
  (string, Score, list of tuples, etc.)
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> player = RealtimeAccompaniment()
>>> player.set_chords("| Dm7 | G7 | Cmaj7 |")
>>> player._score is not None
True
```

#### stop()

Stop playback (future implementation).

* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/builtins/exceptions.html#NotImplementedError) – Real-time playback not yet implemented
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* accompy.Score(measures, title='Untitled', composer='', key='C', time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A musical score containing chord events and metadata.

This is the domain model for chord progressions. It provides a unified
representation regardless of input format (string, iReal URL, tuples, etc.).

### Example

```pycon
>>> score = Score.from_string("| C | Am | F | G |", time_signature=(4, 4))
>>> list(score.measures)
[['C'], ['A-'], ['F'], ['G']]
```

#### *classmethod* from_ireal_url(url)

Parse an iReal Pro URL into a Score.

* **Return type:**
  [`Score`](accompy.base.html.md#accompy.base.Score)

Example::
: url = “irealb://Autumn%20Leaves=…”
  score = Score.from_ireal_url(url)

#### *classmethod* from_string(chord_string, , title='Untitled', key='C', time_signature=(4, 4))

Parse a chord string into a Score.

Supports formats:

- Simple: “C Am F G” (space-separated, one chord per bar)
- Bar lines: “| C | Am | F | G 

  ```
  |
  ```

  ”
- Multi-chord bars: “| C Am | F G 

  ```
  |
  ```

  ” (chords split evenly)
- iReal-style: “C-7 F7 | Bb^7 | Eh7 A7b9 

  ```
  |
  ```

  ”

### Example

```pycon
>>> Score.from_string("| Dm7 | G7 | C^7 | % |").measures  # % means repeat
[['D-7'], ['G7'], ['C^7'], ['C^7']]
```

* **Return type:**
  [`Score`](accompy.base.html.md#accompy.base.Score)

#### to_chord_sequence(, tempo=120)

Convert Score to a ChordSequence (from the converter pipeline).

Each chord gets a duration proportional to its share of the bar.

### Example

```pycon
>>> score = Score.from_string("| Dm7 | G7 | C^7 |")
>>> cs = score.to_chord_sequence(tempo=160)
>>> len(cs)
3
```

### *class* accompy.ScoreToWav(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Callable that renders a [`Score`](#accompy.Score) to a WAV file.

Any function matching this signature can be used as a `score_to_wav`
engine in [`generate_wav()`](#accompy.generate_wav) and [`generate_variations()`](#accompy.generate_variations).

### *class* accompy.SynthesizerBackend(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Audio synthesis backend.

Simpler protocol than AudioRenderer, focused just on synthesis.
Used by the synthesis module.

#### *classmethod* is_available()

Check if this backend’s dependencies are installed.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if the backend can be used

#### render_to_bytes(midi_path, , sample_rate=44100)

Render a MIDI file to PCM bytes (for streaming).

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path to MIDI file
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio sample rate
* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)
* **Returns:**
  Raw PCM audio bytes

#### render_to_file(midi_path, output_path, , sample_rate=44100)

Render a MIDI file to audio.

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path to MIDI file
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Where to save audio
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio sample rate
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created audio file

### accompy.apply_skeleton(cs, skeleton)

Apply a rhythmic skeleton to a chord sequence.

The skeleton defines strike positions within each *measure*. Each strike
plays whatever chord is active at that beat position. If a strike spans a
chord boundary within a measure, it is split so the chord change is
respected.

* **Parameters:**
  * **cs** – A ChordSequence (from `accompy.converters`).
  * **skeleton** (Union[str, tuple, Sequence]) – Skeleton key, name, style, or duration tuple.
* **Return type:**
  ChordSequence
* **Returns:**
  A new ChordSequence with chords expanded according to the skeleton.

### Example

```pycon
>>> from accompy.converters import ChordSequence
>>> cs = ChordSequence([("Dm7", 2.0), ("G7", 2.0)])
>>> result = apply_skeleton(cs, "tresillo")
>>> [(s, d) for s, d in result]
[('Dm7', 1.5), ('Dm7', 0.5), ('G7', 1.0), ('G7', 1.0)]
```

### accompy.check_dependencies()

Check which dependencies are available.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]
* **Returns:**
  Dict mapping dependency name to availability status

### Example

```pycon
>>> deps = check_dependencies()
>>> 'midiutil' in deps
True
```

### accompy.chord_to_notes(symbol)

Convert chord symbol to MIDI notes using the current default resolver.

This is the main entry point for chord resolution in accompy.

* **Parameters:**
  **symbol** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol (e.g., “Dm7”, “G7”)
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  List of MIDI note numbers

### Example

```pycon
>>> notes = chord_to_notes("C")
>>> len(notes) > 0
True
```

### accompy.chords_to_audio(chords, , resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=120, sr=44100, output_path=None)

Convert chord string to audio.

This is the complete pipeline: parse -> resolve -> MIDI -> audio.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Chord resolver (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator (‘pretty_midi’, ‘midiutil’, ‘mido’)
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer (‘pretty_midi’, ‘fluidsynth’, ‘tonal’)
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to SoundFont file
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write WAV file
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData with waveform and sample rate

```pycon
>>> audio = chords_to_audio("| C | Am | F | G |")
>>> audio.write("output.wav")
```

### accompy.chords_to_midi(chords, , resolver=None, midi_gen=None, tempo=120, output_path=None)

Convert chord string to MIDI data.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Resolver name (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator name (‘pretty_midi’, ‘midiutil’, ‘mido’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write MIDI file
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData object

```pycon
>>> md = chords_to_midi("| C | Am | F | G |")
>>> md.to_bytes()[:4]
b'MThd'
```

### accompy.chords_to_notes(chords, , resolver=None, tempo=120)

Convert chord string or ChordSequence to resolved MIDI notes.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Resolver name (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (used if chords is a string)
* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)
* **Returns:**
  NoteSequence with MIDI note numbers

```pycon
>>> ns = chords_to_notes("| C | Am |")
>>> len(ns)
2
>>> all(0 <= n <= 127 for notes, _ in ns for n in notes)
True
```

### accompy.chords_to_sequence(chords, , parser=None, tempo=120, title='', key='C', time_signature=(4, 4))

Parse a chord string into a ChordSequence.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord string in any supported format
  * **parser** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Parser name (‘auto_detect’, ‘plain_text’, ‘chordpro’, ‘musicgen_chord’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (default 120)
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Song title
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Key signature
  * **time_signature** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Time signature tuple
* **Return type:**
  [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)
* **Returns:**
  ChordSequence with parsed chords

```pycon
>>> cs = chords_to_sequence("| Dm7 | G7 | Cmaj7 |", tempo=140)
>>> cs.symbols
['Dm7', 'G7', 'Cmaj7']
>>> cs.tempo
140
```

### accompy.convert(source, target_type, , via=None)

Convert source to target_type using the registered converter.

* **Parameters:**
  * **source** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – The source data
  * **target_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The desired output type
  * **via** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional converter name (uses default if None)
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
* **Returns:**
  Converted data of target_type

Example:

```default
>>> # After converters are registered:
>>> # audio = convert(chord_seq, AudioData)
```

### accompy.diagnose_issues()

Diagnose common setup issues and provide solutions.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Tuple`](https://docs.python.org/3/library/typing.html#typing.Tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  List of (issue, description, solution) tuples

Example:

```default
from accompy.setup_utils import diagnose_issues
for issue, desc, solution in diagnose_issues():
    print(f"{issue}: {desc}")
    print(f"Solution: {solution}")
```

### accompy.ensure_score(chords, , title='Untitled', key='C', time_signature=(4, 4))

Coerce common chord-progression formats into a `Score`.

Supported inputs:

- `Score`: returned as-is
- `str`: chord string (e.g. `"| C | Am | F | G |"`) OR iReal URL (`irealbook://...`)
- `Iterable[tuple[str, int|float]]`: list of `(chord, beats)` like in `accompany`
- `Iterable[str]`: chord symbols, one per bar
- `list[list[str]]`: already-parsed measures

### Notes

- `Score.measures` in `accompy` does not encode per-chord durations within a bar.
  For `(chord, beats)` inputs, durations not equal to whole bars are approximated
  by grouping chords into bars.

### Examples

```pycon
>>> ensure_score("| C | Am | F | G |", time_signature=(4, 4)).measures
[['C'], ['A-'], ['F'], ['G']]
>>> ensure_score([("F#m7b5", 4), ("B7", 4), ("Em", 8)], key="E").measures[:3]
[['F#h7'], ['B7'], ['E-']]
```

* **Return type:**
  [`Score`](accompy.base.html.md#accompy.base.Score)

### accompy.file_to_audio(filepath, , output_path=None, n_repeats=1, transpose=0, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=None, sr=44100)

Convert an iReal Pro HTML/URL file to audio.

Handles:

- iReal Pro HTML files (exported from the app)
- iReal Pro URL strings
- Plain chord text files

Supports repeating the progression and transposing.

* **Parameters:**
  * **filepath** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to an iReal HTML file, or a chord text file
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Where to write audio. If None, uses filepath with .wav extension
  * **n_repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression (default 1)
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose (positive=up, negative=down)
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer backend
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to SoundFont file
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Override BPM (None = use file’s tempo or 120)
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData

Example:

```default
>>> file_to_audio("/path/to/song.html")
>>> file_to_audio("/path/to/song.html", n_repeats=40)
>>> file_to_audio("/path/to/song.html", transpose=5)
```

### accompy.file_to_midi(filepath, , output_path=None, n_repeats=1, transpose=0, resolver=None, midi_gen=None, tempo=None)

Convert an iReal Pro HTML/URL file to MIDI.

Same as file_to_audio but outputs MIDI instead.

* **Parameters:**
  * **filepath** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to an iReal HTML file, or a chord text file
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Where to write MIDI. If None, uses filepath with .mid extension
  * **n_repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Override BPM
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData

### accompy.generate_accompaniment(chords, , style='swing', tempo=120, repeats=1, output_path=None, output_format=None, config=None, use_mma=True, backend=None, autoplay=False)

Generate an accompaniment audio file from a chord progression.

This is the main entry point for accompy. It generates backing tracks
with bass, drums, and piano from chord progressions.

* **Parameters:**
  * **chords** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Chord progression (string, Score, list of tuples, iReal URL)
  * **style** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'swing'`, `'bossa'`, `'rock'`, `'ballad'`, `'funk'`, `'latin'`, `'waltz'`, `'blues'`]) – Musical style (swing, bossa, rock, ballad, funk, latin, waltz, blues)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Where to save the file (None = temp file)
  * **output_format** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'wav'`, `'mp3'`, `'flac'`, `'midi'`, `'mid'`]]) – Output format (wav, mp3, flac, midi)
  * **config** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`AccompanimentConfig`](accompy.base.html.md#accompy.base.AccompanimentConfig)]) – Full configuration object (overrides other params if provided)
  * **use_mma** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True and MMA available, use MMA backend
  * **backend** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'auto'`, `'mma'`, `'builtin'`]]) – Explicitly select backend (‘auto’, ‘mma’, ‘builtin’)
  * **autoplay** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, automatically play the generated audio
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated audio/MIDI file

### Example

```pycon
>>> from accompy import generate_accompaniment
>>> path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=140)
>>> print(f"Generated: {path}")
```

#### NOTE
Requires FluidSynth and a SoundFont for audio rendering.
For MIDI-only output, use output_format=”midi”.

### accompy.generate_mma_wav(score, output_path, , groove='Swing', tempo=120, repeats=1)

Render a Score to WAV using MMA (Musical MIDI Accompaniment).

Accepts any valid MMA groove name (e.g. `"Bebop"`, `"GypsyJazz"`).
Run `mma -Dg` to list available grooves.

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – A [`Score`](#accompy.Score) with chord measures.
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Destination WAV file path.
  * **groove** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – MMA groove name (case-sensitive).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated WAV file.
* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If MMA is not installed or the groove is invalid.

### accompy.generate_variations(score, output_dir, , keys=('C',), tempos=(120,), grooves=('Swing',), repeats=1, filename_template='{title}_{key}_{tempo}bpm_{groove}.wav', score_to_wav=None)

Batch-generate WAV files for many key / tempo / groove combinations.

Produces one WAV for each `(key, tempo, groove)` triple (cycled from the
shortest sequences).  Useful for creating practice backing-track
collections.

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – Base [`Score`](#accompy.Score) (will be transposed per key).
  * **output_dir** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Directory for output files.
  * **keys** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Keys to transpose to.
  * **tempos** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Tempos in BPM to cycle through.
  * **grooves** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Groove / style names to cycle through.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of repeats per file.
  * **filename_template** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Template for filenames. Placeholders:
    `{title}`, `{key}`, `{tempo}`, `{groove}`.
  * **score_to_wav** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ScoreToWav`](accompy.tools.html.md#accompy.tools.ScoreToWav)]) – Engine callable.  Defaults to [`mma_score_to_wav()`](#accompy.mma_score_to_wav).
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]
* **Returns:**
  List of Paths to successfully generated files.

Example:

```default
>>> from accompy import Score, generate_variations
>>> score = Score.from_string("| C6 | Do | C6/E | Fo |", key="C")
>>> generate_variations(
...     score, "/tmp/variations",
...     keys=["C", "G", "F"],
...     tempos=[100, 120],
...     grooves=["Swing", "BossaNova"],
... )

>>> # With a custom engine:
>>> from accompy.tools import make_converter_engine
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_variations(
...     score, "/tmp/variations",
...     keys=["C", "G"],
...     tempos=[100, 120],
...     grooves=["Swing"],
...     score_to_wav=engine,
... )
```

### accompy.generate_wav(score, output_path, , groove='Swing', tempo=120, repeats=1, score_to_wav=None)

Generate a WAV file from a Score using a pluggable engine.

By default uses MMA (Musical MIDI Accompaniment).  Pass a custom
`score_to_wav` callable to use a different backend — for instance one
built with [`make_converter_engine()`](#accompy.make_converter_engine).

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – A [`Score`](#accompy.Score) with chord measures.
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Destination WAV file path.
  * **groove** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Groove / style name (interpretation depends on the engine).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression.
  * **score_to_wav** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ScoreToWav`](accompy.tools.html.md#accompy.tools.ScoreToWav)]) – Engine callable.  Defaults to [`mma_score_to_wav()`](#accompy.mma_score_to_wav).
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated WAV file.

Example:

```default
>>> from accompy import Score, generate_wav
>>> score = Score.from_string("| Dm7 | G7 | C^7 |")
>>> generate_wav(score, "/tmp/test.wav", groove="BossaNova", tempo=140)
PosixPath('/tmp/test.wav')

>>> # With a custom engine:
>>> from accompy.tools import make_converter_engine
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_wav(score, "/tmp/test.wav", score_to_wav=engine, tempo=140)
```

### accompy.get_app_folder(, folder_kind='data')

Return the app directory for *folder_kind*, creating it if needed.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### accompy.get_artifact_dir(kind)

Return (and create) an artifact sub-directory for *kind*.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### accompy.get_chord_resolver()

Get the current default chord resolver.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]]
* **Returns:**
  The active chord resolution function

### Example

```pycon
>>> resolver = get_chord_resolver()
>>> notes = resolver("C")
>>> len(notes) > 0
True
```

### accompy.get_config(name)

Return a config file path, seeding from package data if missing.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### accompy.get_pattern_registry()

Get the global pattern registry, initializing if needed.

* **Return type:**
  [`PatternRegistry`](accompy.patterns.html.md#accompy.patterns.PatternRegistry)
* **Returns:**
  The global PatternRegistry instance

### Example

```pycon
>>> registry = get_pattern_registry()
>>> 'swing' in registry
True
```

### accompy.get_patterns(style)

Get all patterns for a given style.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  Dict with ‘drums’, ‘bass’, ‘comp’ keys containing pattern lists

### Example

```pycon
>>> patterns = get_patterns("bossa")
>>> drums = patterns["drums"][0]
>>> drums.name
'bossa'
```

### accompy.get_resource(name)

Return a user resource path, seeding from package data if missing.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### accompy.list_available_converters()

List all available converters organized by pipeline stage.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Dict mapping stage names to lists of converter names.

```pycon
>>> info = list_available_converters()
>>> 'parsers' in info
True
>>> 'resolvers' in info
True
```

### accompy.list_skeletons(, beats_per_measure=None, style=None)

List available skeleton keys, optionally filtered.

* **Parameters:**
  * **beats_per_measure** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter to skeletons matching this measure length.
  * **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter to skeletons associated with this style.
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of skeleton key strings.

### Examples

```pycon
>>> "tresillo" in list_skeletons()
True
>>> all(RHYTHMIC_SKELETONS[k]["beats_per_measure"] == 3
...     for k in list_skeletons(beats_per_measure=3))
True
```

### accompy.load_resource_json(name)

Read a resource file as JSON.

### accompy.load_resource_lines(name)

Read a resource file as a list of non-empty stripped lines.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### accompy.load_resource_text(name)

Read a resource file as text.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### accompy.make_converter_engine(, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, sr=44100)

Create a [`ScoreToWav`](#accompy.ScoreToWav) engine from accompy’s converter pipeline.

This wraps the `ChordSequence → NoteSequence → MidiData → AudioData`
converter chain into the same interface that [`generate_wav()`](#accompy.generate_wav) expects,
so you can swap it in place of the default MMA engine.

* **Parameters:**
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Chord resolver name (e.g. `"pychord"`, `"tonal"`).
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator name (e.g. `"pretty_midi"`, `"midiutil"`).
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer name (e.g. `"fluidsynth"`, `"pretty_midi"`).
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to a SoundFont file (for FluidSynth-based renderers).
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate.
* **Return type:**
  [`ScoreToWav`](accompy.tools.html.md#accompy.tools.ScoreToWav)
* **Returns:**
  A callable matching the [`ScoreToWav`](#accompy.ScoreToWav) protocol.

Example:

```default
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_wav(score, "/tmp/out.wav", score_to_wav=engine, tempo=120)
```

### accompy.midi_to_audio(midi_data, , audio_renderer=None, soundfont=None, sr=44100, output_path=None)

Convert MidiData to audio.

* **Parameters:**
  * **midi_data** ([`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)) – MidiData object
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer name
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to SoundFont file
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write WAV file
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData

```pycon
>>> audio = midi_to_audio(some_midi_data)
```

### accompy.mma_score_to_wav(score, output_path, , groove='Swing', tempo=120, repeats=1)

Render a Score to WAV using MMA (Musical MIDI Accompaniment).

Accepts any valid MMA groove name (e.g. `"Bebop"`, `"GypsyJazz"`).
Run `mma -Dg` to list available grooves.

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – A [`Score`](#accompy.Score) with chord measures.
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Destination WAV file path.
  * **groove** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – MMA groove name (case-sensitive).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated WAV file.
* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If MMA is not installed or the groove is invalid.

### accompy.parse_ireal_html(html_path)

Extract a Score from an iReal Pro HTML export file.

iReal Pro can export songs as HTML files containing an `irealb://` link.
This function reads the file, extracts that link, and parses it into a
[`Score`](#accompy.Score).

* **Parameters:**
  **html_path** (str) – Path to the HTML file exported from iReal Pro.
* **Return type:**
  Score
* **Returns:**
  A Score with measures, title, key, and time signature.
* **Raises:**
  * [**FileNotFoundError**](https://docs.python.org/3/builtins/exceptions.html#FileNotFoundError) – If *html_path* does not exist.
  * [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If no iReal URL is found in the HTML.

Example:

```default
>>> score = parse_ireal_html("/path/to/song.html")
>>> score.title
'Autumn Leaves'
```

### accompy.parse_ireal_url(url)

Parse an iReal Pro URL into a Score object.

Tries pyRealParser’s `parse_ireal_url` first, then falls back to
constructing a `Tune` directly (handles URLs with empty `==` fields),
and finally to a no-dependency best-effort parser.

### accompy.play_audio(audio_path)

Play an audio file using the system’s default audio player.

* **Parameters:**
  **audio_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Path to the audio file
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if playback started successfully, False otherwise

### Example

```pycon
>>> from accompy import play_audio
>>> play_audio("/path/to/audio.wav")
```

### accompy.print_diagnostic_report()

Print a comprehensive diagnostic report.

### accompy.print_setup_instructions()

Print installation instructions for missing dependencies.

### accompy.register_skeleton(key, pattern, , name='', beats_per_measure=None, styles=None)

Register a custom rhythmic skeleton.

* **Parameters:**
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Unique string key for the skeleton.
  * **pattern** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)) – Tuple of beat durations.
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Human-readable name (defaults to key).
  * **beats_per_measure** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Measure length in beats (defaults to sum of pattern).
  * **styles** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – List of associated style strings.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> register_skeleton("my_groove", (1, 0.5, 0.5, 2), name="My Groove")
>>> resolve_skeleton("my_groove")
(1, 0.5, 0.5, 2)
```

### accompy.register_style(style, drums, bass, comp)

Register a custom style with the global registry.

* **Parameters:**
  * **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Style name
  * **drums** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of DrumPattern objects
  * **bass** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of BassPattern objects
  * **comp** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of CompingPattern objects
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> registry = get_pattern_registry()
>>> register_style('my_funk', [my_drum_pattern], [my_bass_pattern], [])
```

### accompy.render_chords(chords, , rhythmic_skeleton='whole_note', bpm=100, transpose=0, n_loops=None, max_seconds=None, ai_enhance=True, suno_mode='cover', prompt_template='{genre} backing track with {instruments}', genre='jazz', instruments=None, audio_weight=0.99, style_weight=0.51, weirdness=0.0, model='', instrumental=True, wait_for_completion=True, poll_interval=15.0, timeout=600.0, chords_to_midi_audio=None, audio_to_enhanced_audio=None, midi_store=None, midi_audio_store=None, enhanced_audio_store=None, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, sr=44100)

Render chords to a high-quality audio file, optionally AI-enhanced.

* **Parameters:**
  * **chords** – Chord input — string (`"| Dm7 | G7 | C^7 |"`), iReal URL,
    [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence), [`Score`](accompy.base.html.md#accompy.base.Score),
    or list of `(chord, beats)` tuples.
  * **rhythmic_skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Restrike pattern within each measure.
  * **bpm** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in beats per minute.
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose (positive=up, negative=down).
  * **n_loops** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Explicit number of loops. Mutually exclusive with *max_seconds*.
  * **max_seconds** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Target maximum duration; computes loop count automatically.
    Defaults to 210 (3.5 min) when neither *n_loops* nor *max_seconds*
    is given.
  * **ai_enhance** (`Union`[[`bool`](https://docs.python.org/3/builtins/functions.html#bool), [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – `True` for default Suno enhancement, `False`/`None`
    to skip, or a callable `(audio_path, prompt, **kw) → bytes`.
  * **suno_mode** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – `"cover"` (default, re-generates in style) or `"extend"`.
  * **prompt_template** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Template with `{genre}` and `{instruments}` placeholders.
  * **genre** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Genre/style tags for the AI prompt.
  * **instruments** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Instrument list for the AI prompt. Defaults to
    `["piano", "bass", "drums"]`.
  * **audio_weight** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – How much the source audio influences AI output (0–1).
  * **style_weight** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – How much the style prompt influences AI output (0–1).
  * **weirdness** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Creative deviation for cover mode (0–1).
  * **model** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Suno model version (e.g. `"V4_5"`).
  * **instrumental** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, generate without vocals.
  * **wait_for_completion** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, poll until AI generation is ready.
  * **poll_interval** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds between AI status checks.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Max seconds to wait for AI completion.
  * **chords_to_midi_audio** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)]) – Override for the MIDI audio rendering step.
    Callable: `(ChordSequence, **kw) → AudioData`.
  * **audio_to_enhanced_audio** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)]) – Override for the AI enhancement step.
    Callable: `(audio_path, prompt, **kw) → bytes`.
  * **midi_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional store for MIDI files. `None` = don’t persist MIDI.
  * **midi_audio_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Store for rendered MIDI audio. `None` = default
    file store under `~/.local/share/accompy/artifacts/midi_audio/`.
  * **enhanced_audio_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Store for AI-enhanced audio. `None` = default
    file store under `~/.local/share/accompy/artifacts/enhanced_audio/`.
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend name.
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend name.
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer backend name.
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to a SoundFont file.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate for MIDI audio rendering.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Filesystem path to the final audio file.

### accompy.render_chords_batch(configs, \*\*shared_kwargs)

Run [`render_chords()`](#accompy.render_chords) for each config dict.

Each dict in *configs* is merged with *shared_kwargs* (per-config values
take priority over shared defaults).

* **Parameters:**
  * **configs** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Iterable of dicts, each containing keyword arguments for
    [`render_chords()`](#accompy.render_chords).
  * **\*\*shared_kwargs** – Default arguments applied to every config.
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of filesystem paths to the final audio files.

Example:

```default
>>> from itertools import product
>>> configs = [
...     dict(chords="| Dm7 | G7 | C^7 |", genre=g, bpm=b)
...     for g, b in product(["jazz", "lofi"], [100, 120])
... ]
>>> paths = render_chords_batch(configs, ai_enhance=False)
```

### accompy.resolve_skeleton(skeleton)

Resolve a skeleton specification to a tuple of durations.

Accepts:

> - A tuple or list of numbers (pass-through)
> - A skeleton key (e.g., `"tresillo"`, `"whole_note"`)
> - A skeleton name, case-insensitive (e.g., `"Tresillo"`)
> - A style string (e.g., `"reggae"`) — returns the first match
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)
* **Returns:**
  Tuple of beat durations summing to the measure length.
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If the skeleton cannot be resolved.

### Examples

```pycon
>>> resolve_skeleton("whole_note")
(4,)
>>> resolve_skeleton("tresillo")
(1.5, 1.5, 1)
>>> resolve_skeleton((2, 2))
(2, 2)
>>> resolve_skeleton("Dotted half + quarter")
(3, 1)
```

### accompy.rhythm_to_audio(chords, , skeleton='whole_note', resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=120, sr=44100, output_path=None)

Convert chords to audio using a rhythmic skeleton for restrike timing.

Same as [`rhythm_to_midi()`](#accompy.rhythm_to_midi) but renders all the way to audio.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence.
  * **skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Skeleton key, name, style, or duration tuple.
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver name.
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator name.
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer name.
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to SoundFont file.
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate.
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional path to write WAV file.
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData with waveform and sample rate.

### Example

```pycon
>>> audio = rhythm_to_audio("| C | Am |", skeleton="half_notes")
```

### accompy.rhythm_to_midi(chords, , skeleton='whole_note', resolver=None, midi_gen=None, tempo=120, output_path=None)

Convert chords to MIDI using a rhythmic skeleton for restrike timing.

The skeleton defines when chords are struck within each measure. Each
chord is sustained for the skeleton’s duration at that beat position.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string (e.g., `"| Dm7 | G7 | Cmaj7 |"`) or ChordSequence.
  * **skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Skeleton key, name, style, or duration tuple.
    Defaults to `"whole_note"` (one strike per measure).
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver name (e.g., `"pychord"`, `"tonal"`).
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator name (e.g., `"pretty_midi"`, `"midiutil"`).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (used if chords is a string).
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional path to write MIDI file.
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData object.

### Example

```pycon
>>> md = rhythm_to_midi("| C | Am | F | G |", skeleton="tresillo")
>>> md.to_bytes()[:4]
b'MThd'
```

### accompy.set_chord_resolver(resolver)

Set the default chord resolver.

This enables global customization of chord-to-notes resolution.

* **Parameters:**
  **resolver** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]]) – A function that takes a chord symbol (str) and returns MIDI notes (list[int])
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> def my_resolver(symbol: str) -> list[int]:
...     # Custom chord voicing logic
...     return [60, 64, 67]  # C major triad
>>> set_chord_resolver(my_resolver)
```

### accompy.setup_soundfont(force=False)

Download and configure a SoundFont file.

* **Parameters:**
  **force** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, download even if a SoundFont already exists
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if successful, False otherwise

Example:

```default
from accompy.setup_utils import setup_soundfont
if setup_soundfont():
    print("SoundFont configured successfully!")
```

### accompy.tonal_resolver(symbol, , transpose=-12)

Resolve chord symbol to MIDI notes using the tonal package (default).

The tonal package is lightweight and designed for music theory operations.
It anchors chord roots around C4=60. We apply a default -12 semitone transpose
to voice chords closer to C3=48 for better bass/piano range.

* **Parameters:**
  * **symbol** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol (e.g., “Dm7”, “G7”, “Cmaj7”)
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitone offset to apply (default: -12)
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  List of MIDI note numbers

### Example

```pycon
>>> notes = tonal_resolver("Cmaj7")
>>> len(notes) > 0
True
```

#### NOTE
Requires: pip install tonal
See: [https://github.com/thorwhalen/tonal](https://github.com/thorwhalen/tonal)

### accompy.transpose_chord(chord, semitones, , use_flat=None)

Transpose a chord symbol by *semitones*.

Handles slash chords (e.g. `"C6/E"`).

* **Parameters:**
  * **chord** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol like `"Am7"`, `"C6/E"`, `"G#o"`.
  * **semitones** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of semitones.
  * **use_flat** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – Force flat/sharp spelling (see [`transpose_note()`](#accompy.transpose_note)).
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> transpose_chord("Am7", 2)
'Bm7'
>>> transpose_chord("C6/E", 5)
'F6/A'
>>> transpose_chord("G#o", -2, use_flat=True)
'Gbo'
```

### accompy.transpose_note(name, semitones, , use_flat=None)

Transpose a single note name by *semitones*.

* **Parameters:**
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Note name like `"C"`, `"Eb"`, `"F#"`.
  * **semitones** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of semitones (positive = up, negative = down).
  * **use_flat** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – Force flat (True) or sharp (False) spelling.
    `None` (default) uses flats for downward transposition.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> transpose_note("C", 5)
'F'
>>> transpose_note("A", -2)
'G'
>>> transpose_note("C", 1, use_flat=True)
'Db'
```

### accompy.transpose_score(score, target_key)

Transpose a [`Score`](#accompy.Score) to a new key.

The spelling (sharp vs flat) is chosen automatically based on the
*target_key*.

* **Parameters:**
  * **score** – A [`Score`](#accompy.Score) instance.
  * **target_key** (str) – Target key, e.g. `"Eb"`, `"G"`, `"F#"`.
* **Return type:**
  Score
* **Returns:**
  A new Score in the target key with an updated title.

### Example

```pycon
>>> from accompy import Score
>>> s = Score.from_string("| C | Am | F | G |", key="C")
>>> t = transpose_score(s, "G")
>>> [m[0] for m in t.measures]
['G', 'E-', 'C', 'D']
```

### accompy.verify_and_setup(interactive=True, auto_fix=False)

Verify all dependencies and optionally auto-configure.

* **Parameters:**
  * **interactive** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, prompt user for permission before making changes
  * **auto_fix** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True and interactive=False, automatically fix issues without prompting
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]
* **Returns:**
  Dict mapping dependency name to whether it’s available

### Example

```pycon
>>> from accompy.setup_utils import verify_and_setup
>>> status = verify_and_setup(interactive=False)
>>> if all(status.values()):
...     print("Ready to use!")
```

### Modules

| [`audio_renderers`](accompy.audio_renderers.html.md#module-accompy.audio_renderers)       | Audio renderers — convert MidiData to AudioData.                                |
|-------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`base`](accompy.base.html.md#module-accompy.base)                             | Core domain models for accompy.                                                 |
| [`chord_parsers`](accompy.chord_parsers.html.md#module-accompy.chord_parsers)           | Chord sheet parsers — convert various text formats to ChordSequence.            |
| [`chord_resolution`](accompy.chord_resolution.html.md#module-accompy.chord_resolution)     | Chord symbol to MIDI notes resolution.                                          |
| [`chord_resolvers`](accompy.chord_resolvers.html.md#module-accompy.chord_resolvers)       | Chord resolvers — convert chord symbols to MIDI note numbers.                   |
| [`converters`](accompy.converters.html.md#module-accompy.converters)                 | Core types for the chord-to-audio pipeline.                                     |
| [`data_access`](accompy.data_access.html.md#module-accompy.data_access)               | Per-user data directory management for accompy.                                 |
| [`main`](accompy.main.html.md#module-accompy.main)                             | Main accompaniment generation module.                                           |
| [`midi_generators`](accompy.midi_generators.html.md#module-accompy.midi_generators)       | MIDI generators — convert NoteSequence to MidiData.                             |
| [`patterns`](accompy.patterns.html.md#module-accompy.patterns)                     | Pattern registry and access for accompany patterns.                             |
| [`pipeline`](accompy.pipeline.html.md#module-accompy.pipeline)                     | High-level pipeline API — one-call chord-to-audio conversion.                   |
| [`protocols`](accompy.protocols.html.md#module-accompy.protocols)                   | Protocols defining extensibility contracts for accompy.                         |
| [`realtime`](accompy.realtime.html.md#module-accompy.realtime)                     | Real-time accompaniment support (foundation).                                   |
| [`renderers`](accompy.renderers.html.md#module-accompy.renderers)                   | MIDI and MMA rendering backends for accompy.                                    |
| [`rendering`](accompy.rendering.html.md#module-accompy.rendering)                   | High-quality chord rendering pipeline — from chord charts to AI-enhanced audio. |
| [`rhythmic_skeletons`](accompy.rhythmic_skeletons.html.md#module-accompy.rhythmic_skeletons) | Rhythmic skeletons — duration-only measure patterns for simple accompaniment.   |
| [`setup_utils`](accompy.setup_utils.html.md#module-accompy.setup_utils)               | Setup and configuration utilities for accompy.                                  |
| [`synthesis`](accompy.synthesis.html.md#module-accompy.synthesis)                   | Audio synthesis backends for accompy.                                           |
| [`tools`](accompy.tools.html.md#module-accompy.tools)                           | Tools for generating accompaniment audio from Score objects.                    |
| [`util`](accompy.util.html.md#module-accompy.util)                             | Utility functions for chord parsing and normalization.                          |
| [`wips`](accompy.wips.html.md#module-accompy.wips)                             | Backward-compatibility shim — wips modules have moved to accompy top level.     |
