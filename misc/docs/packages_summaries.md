# Accompy Package Summary

## Overview

Generate backing track audio/MIDI from chord charts, like iReal Pro. Supports styles (swing/bossa/rock/etc), iReal URLs, multi-instrument (drums/bass/piano), backends (builtin/MMA).

Key features: Simple API, flexible inputs (strings/Score/tuples/URLs), custom patterns, setup verification, tests.

## Modules/Files

- README.md: Usage, install, chord notation, examples.
- accompy/__init__.py: generate_accompaniment, Score, ensure_score.
- accompy/patterns/: pattern registry API (`__init__.py`), pattern data (`builtin.py`), and dataclasses/constants (`dataclasses.py`).
- tests/test_patterns.py: Unit tests for patterns/validation.

## Key Functions/Classes
- def generate_accompaniment(chords: str|Score|list[tuple]|None, style='swing', tempo=120, repeats=1, output_path: str=None, backend='auto') -> str: 
  """Generate audio/MIDI. e.g., generate_accompaniment('| Dm7 | G7 |', style='bossa') -> WAV path."""
  Params: chords (string/Score/tuples/URL), style, tempo, repeats, path (.wav/.mid), backend (auto/builtin/mma). Returns: file path.

- class Score: From chord data. Methods: from_string(chords, title='', key='', time_signature=(4,4)) -> Score.
- def ensure_score(input: various) -> Score: Convert to Score.

- def get_patterns(style: str) -> dict[str, list[Pattern]]: 
  """Patterns for style. Returns {'drums': [...], 'bass': [...], 'comp': [...]}. Raises KeyError if unknown."""
  Params: style (swing/bossa/etc). Returns: dict of Pattern lists (hits/notes per bar).

- def verify_and_setup(): Interactive dependency setup.
- def check_dependencies() -> bool: Check FluidSynth/SoundFont.
- def print_diagnostic_report(): Detailed setup report.

## Usage Tips
- Imports: from accompy import generate_accompaniment, Score.
- Dependencies: fluidsynth (audio), midiutil/mingus (MIDI), pyRealParser (optional iReal URLs). System: FluidSynth/SoundFont.
- Patterns: Extend with custom styles/patterns. Use backend='mma' if MMA installed for advanced.
- Notes: Chord notation: ^7=maj7, -7=min7, % repeat. Tests cover patterns/validation.

## Examples
audio = generate_accompaniment('| C | Am | F | G |', style='rock', tempo=140, output_path='track.wav')

score = Score.from_string('| Dm7 G7 | Cmaj7 |', title='ii-V-I')
midi = generate_accompaniment(score, output_path='track.mid')  # MIDI only

patterns = get_patterns('bossa')  # {'drums': [Pattern(hits=...)], ...}


-------------------------------------------------------

# Hum Package Summary

## Overview
Python synthesizer for audio signals using Pyo. Features real-time param control, event recording/playback/rendering, context management. Includes utils for time formatting, waveform plotting.

Key features: Synth wrapper for Pyo, dials/settings distinction, event handling, WAV decoding/plotting.

## Modules/Files
- README.md: Synth examples, interactive REPL, dials/settings.
- pyo_util.py: Synth class, simple_sine, noise_synth, etc.
- extra_util.py: estimate_frequencies.
- utils/date_ticks.py: Time utils (utc_datetime_from_val_and_unit, strftime_with_precision, str_ticks).
- utils/plotting.py: Waveform plotting (plot_wf, disp_wf).
- setup.py: Installation.

## Key Functions/Classes
- class Synth(synth_func: callable = None, **kwargs): 
  """Wrapper for Pyo synths with real-time control, recording. e.g., @Synth(dials='freq') def my_synth(freq=440): return Sine(freq)"""
  Params: synth_func (returns Pyo obj), dials/settings (strs), sr=44100, etc. Methods: start(), stop(), get_recording(), render_events(events) -> WAV bytes.

- def simple_sine(freq=220): Returns Sine(freq). Example synth.
- def noise_synth(cutoff=1000, q=1, volume=0.2, type=0): Noise with Biquadx filter.

- def round_event_times(events, round_to=0.1) -> list: Round timestamps.
- def estimate_frequencies(wf, sr, **kwargs) -> freqs: Freq estimation.

- def utc_datetime_from_val_and_unit(val: float, unit: str) -> datetime: Convert val (e.g., seconds) to datetime.
- def strftime_with_precision(tick: datetime, format: str, sub_secs_precision=2) -> str: Format datetime with precision.
- def str_ticks(ticks: list[float], ticks_unit: str, sub_secs_precision=2) -> list[str]: Format ticks as strs.

- def plot_wf(wf: array, sr=44100, figsize=(22,5), offset_s=0, ax=None, **kwargs): Plot waveform with time axis.
- def disp_wf(wf: array|bytes, sr=44100, autoplay=False, wf_plot_func=plot_wf): Display audio in Jupyter (uses IPython.Audio).

## Usage Tips
- Imports: from hum.pyo_util import Synth; from hum.utils.plotting import disp_wf.
- Dependencies: pyo (for Synth), recode (WAV decode), numpy/matplotlib (plotting), IPython (disp).
- Patterns: Use with context: with Synth(simple_sine) as s: s(freq=440); time.sleep(1). Favor dials for smooth changes.
- Notes: Events are list[(time, dict[params])]. Render to WAV bytes for saving/playing.

## Examples
from hum.pyo_util import Synth
@Synth() def sine(freq=440): return Sine(freq)
with sine as s: s(freq=660); time.sleep(1)  # Changes freq

events = s.get_recording()  # List of timed param changes
wav = s.render_events(events)  # Bytes

from hum.utils.plotting import disp_wf
disp_wf(wav, autoplay=True)  # Plays in Jupyter



-------------------------------------------------------

# Sonification Package Summary

## Overview
Map data (e.g., DataFrames) to sound for auditory interpretation. Normalizes data, generates tones, combines waveforms. Includes astronify-style sonification.

Key features: Preprocess DF (normalize/encode), map cols to pitch/dur/vol, generate/save WAV, combine multi-col sonifications.

## Modules/Files
- README.md: DF to audio example.
- docsrc/conf.py: Sphinx config (project info, extensions like autodoc/napoleon).
- sonification/__init__.py: Main functions (preprocess_dataframe, generate_tone, map_features_to_audio, sonification_dataframe).
- sonification/astronify.py: sonify_dataframe_w_astronify, combine_waveforms.
- sonification/util.py: Config getter, default paths (MIDI/WAV outputs).

## Key Functions/Classes
- def preprocess_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]: 
  """Normalize nums, add min dur, encode categoricals. Returns df, label_encoders."""
  Params: df. Returns: processed df, encoders dict.

- def generate_tone(frequency: float, duration: float, volume: float, sample_rate=44100) -> np.array: 
  """Sine wave tone. e.g., generate_tone(440, 0.5, 0.7) -> wave array."""
  Params: freq, dur, vol, sr. Returns: waveform.

- def map_features_to_audio(df: pd.DataFrame, pitch_col: str, duration_col: str, volume_col: str, sample_rate=44100) -> tuple[np.array, int]: 
  """Map DF cols to tones, concat waves. Freq = 440 + pitch*440."""
  Params: df, col names, sr. Returns: waveform, sr.

- def save_or_return_audio(waveform: np.array, sample_rate: int, filepath: str = None): Saves to file or returns wave/sr.
- def sonification_dataframe(df: pd.DataFrame, pitch_col: str, duration_col: str, volume_col: str, sample_rate=44100, filepath: str = None): 
  """Full pipeline: preprocess + map + save/return."""

- def sonify_dataframe_w_astronify(df: pd.DataFrame, columns: list[str] = None, combine: bool = True, **kwargs) -> np.array | dict: 
  """Astronify-style: Sonify cols separately, optional combine. e.g., sonify_dataframe_w_astronify(df, ['x', 'y'])"""
  Params: df, columns (all if None), combine. Returns: wave or dict[col: {'waveform', 'sr'}].

- def combine_waveforms(sonifications: dict[str, dict], weights: dict[str, float] = None) -> np.array: 
  """Mix waveforms with weights (normalize to 1). e.g., combine_waveforms(soni_dict, {'col1': 0.6})"""
  Params: soni dict, weights (default equal). Returns: combined wave.

## Usage Tips
- Imports: from sonification import sonification_dataframe, sonify_dataframe_w_astronify.
- Dependencies: numpy, pandas, sklearn (MinMaxScaler, LabelEncoder), simpleaudio (save/play), scipy.signal (in astronify).
- Patterns: Use with simpleaudio.play_buffer for playback. Config via config2py for paths.
- Notes: Waves are float arrays; normalize to int16 for playback. Supports custom waveforms (sine/square/etc in astronify).

## Examples
df = pd.DataFrame({'pitch': [0.2,0.4], 'duration': [0.5,0.5], 'volume': [0.5,0.7]})
wave, sr = sonification_dataframe(df, 'pitch', 'duration', 'volume')
sa.play_buffer(np.int16(wave / np.max(np.abs(wave)) * 32767), 1, 2, sr)  # Play

from sonification.astronify import sonify_dataframe_w_astronify
wave = sonify_dataframe_w_astronify(df, ['pitch', 'volume'], combine=True)  # Combined



-------------------------------------------------------

# Sung Package Summary

## Overview
Music data access from chords/lyrics datasets, Spotify API (playlists/tracks), Wikipedia. Tools for parsing/rendering chord sheets (text/PDF), searching songs.

Key features: Chord/lyrics dataset (search/load), filter/pack text, PDF styling, Spotify creds setup, track/playlist ID casting, DF column moving.

## Modules/Files
- README.md: Chords/lyrics processing, Spotify setup/usage.
- chords_lyrics.py: Parsing/rendering (render_chords_and_lyrics, parse_chord_lyrics, remove_non_lyrics, pack_song_text).
- spotify.py: API access (cast_track_key, ensure_playlist_id, move_columns_to_front/back).

## Key Functions/Classes
- def render_chords_and_lyrics(raw_text: str, to: str='text', output_path: str=None, filter_non_lyrics: bool=False, pack_lines: bool=False, max_line_length=80, **pdf_kwargs): 
  """Render chord sheet to text/PDF. e.g., render_chords_and_lyrics(text, to='pdf', page_size='A4')"""
  Params: raw_text, to (text/pdf), path, filters, PDF styles (fonts/margins). Returns: str or saves file.

- def search_songs(title: str=None, artist: str=None, lyrics: str=None) -> pd.DataFrame: 
  """Search dataset. e.g., search_songs(title='wonderwall', artist='oasis') -> DF with chords&lyrics."""
  Params: criteria. Returns: Filtered DF.

- def get_lyrics_and_chords_dataset() -> pd.DataFrame: Load full dataset (cached).

- def remove_non_lyrics(text: str, keep_metadata_lines: bool=False) -> str: 
  """Remove non-lyrics (headers/metadata)."""

- def pack_song_text(text: str, max_length=80) -> str: Combine short lines.

- def parse_chord_lyrics(text: str) -> structured data: Parse to groups/lines.

- def extract_title(text: str) -> str: Get song title.

- def cast_track_key(track_key: str, src_kind: str=None, target_kind: str='id') -> str: 
  """Convert track refs (URI/URL/ID/HREF). e.g., cast_track_key('spotify:track:xxx', target_kind='url')"""
  Params: key, src_kind (detect if None), target_kind. Returns: formatted key.

- def ensure_track_id(key: str) -> str: To ID.
- def ensure_playlist_id(spec: str) -> str: To playlist ID.

- def move_columns_to_front(df: pd.DataFrame, columns: list[str], allow_excess=True) -> pd.DataFrame: 
  """Reorder DF cols to front. e.g., move_columns_to_front(df, ['name', 'artist'])"""
- def move_columns_to_back(df: pd.DataFrame, columns: list[str], allow_excess=True) -> pd.DataFrame: To back.

## Usage Tips
- Imports: from sung import render_chords_and_lyrics, search_songs, get_lyrics_and_chords_dataset.
- Dependencies: pandas (DFs), reportlab (PDF), re (parsing). Spotify: spotipy (API), env vars for creds.
- Patterns: Use env exports for Spotify. Combine with hum for audio from lyrics.
- Notes: Dataset has thousands of songs. PDF uses Helvetica/Times fonts by default.

## Examples
songs = search_songs(title='hotel california')
text = songs.iloc[0]['chords&lyrics']
render_chords_and_lyrics(text, to='pdf', output_path='song.pdf')  # PDF

from sung import cast_track_key
url = cast_track_key('4iV5W9uYEdYUVa79Axb7Rh', src_kind='id', target_kind='url')  # https://open.spotify.com/track/...



-------------------------------------------------------

# Theremin Package Summary

## Overview
Modular framework for mapping sensors (video gestures/keyboard) to audio. Pipelines: Feature extraction (MediaPipe hands), mapping to params, synthesis (Pyo). Pre-built pipelines (theremin/two_voice).

Key features: Hand tracking (positions/gestures/openness/pinch), param mappings (freq/vol/vibrato), synths (sine/theremin/FM), CLI/app.

## Modules/Files
- ARCHITECTURE.md: Pipeline overview, components (FeatureMapping/AudioFeatureBuilder/AudioPipeline).
- theremin/__init__.py: run_theremin_app (CLI entry).
- audio.py: Synths (theremin_synth, two_hand_synth, simple_sine, fm_synth).
- audio_features.py: Builders/mappings (create_theremin_builder, FeatureMapping, range_transformer).
- pipelines.py: AudioPipeline class, ALL_PIPELINES (theremin/simple_sine/etc), validate.
- readers.py: Sensor readers (video_reader, keyboard_reader).
- video_features.py: Hand features (many_video_features, many_single_hand_features: landmarks/wrist/palm/fingers/normal/openness/pinch).

## Key Functions/Classes
- def run_theremin_app(pipeline: str='theremin', **kwargs): 
  """CLI app entry. e.g., run_theremin_app('two_voice', video_src=0)"""
  Params: pipeline name, video_src (cam/file), reader ('video'/'keyboard'), etc.

- class AudioPipeline(name: str, audio_features: callable, synth: callable): 
  """Video->features->audio params->synth. e.g., AudioPipeline('custom', builder, sine_synth)"""
  Methods: validate() -> issues list, __call__(video_features) -> audio.

- def create_theremin_builder() -> AudioFeatureBuilder: Maps wrists to freq/vol, openness to vibrato.
- class FeatureMapping(audio_param: str, video_feature: str, transform: callable = identity, default: float = None): Single mapping.
- def range_transformer(input_range: tuple, output_range: tuple) -> callable: Linear map.

- def theremin_synth(freq=440, volume=0.5, vibrato_depth=0, vibrato_rate=5) -> Pyo obj: Theremin sound.
- def two_hand_synth(freq1=440, freq2=660, volume=0.5) -> Pyo: Two voices.
- def fm_synth(carrier_freq=440, mod_freq=440, mod_index=5, volume=0.5) -> Pyo: FM synth.

- def video_reader(src=0, **kwargs) -> gen: Yield frames from cam/file.
- def keyboard_reader(**kwargs) -> gen: Yield key presses.

- def many_video_features(hand_detection, include=set('wrist_position', ...), exclude=()) -> dict: 
  """Extract hand features (l_/r_ prefixes): landmarks/wrist/palm/fingers/normal/handedness/gesture/openness/pinch/etc."""
  Params: MediaPipe detection, include/exclude sets. Returns: dict with prefixes.

## Usage Tips
- Imports: from theremin import run_theremin_app; from theremin.pipelines import ALL_PIPELINES, AudioPipeline.
- Dependencies: cv2 (video), mediapipe (hands), pyo (synth), hum (optional for advanced synth).
- Patterns: Run CLI: python -m theremin --pipeline theremin. Custom: pipeline = AudioPipeline(...); pipeline(video_features).
- Notes: Features use MediaPipe indices (WRIST=0, etc). Validate pipelines for mismatches.

## Examples
from theremin import run_theremin_app
run_theremin_app('theremin')  # Webcam to theremin sound

from theremin.audio_features import create_theremin_builder
builder = create_theremin_builder()
audio_params = builder({'r_wrist_position': [0.5, 0.3], 'l_wrist_position': [0.2, 0.7]})  # {'freq': ..., 'volume': ...}

from theremin.video_features import many_video_features
features = many_video_features(mediapipe_detection)  # {'r_wrist_position': ..., 'l_openness': ...}



-------------------------------------------------------

# Tonal Package Summary

## Overview
Tools for music analysis and generation, including scales, notes, MIDI conversion, chord sequences to audio, counterpoint translation, and score manipulation. Depends on music21 for core music objects.

Key features: Register custom scales/chords, list available qualities, generate WAV from chords, translate notes within scales, filter/delete score parts.

## Modules/Files
- README.md: Examples for notes, chords, counterpoint.
- notes.py: Scale/MIDI utilities (scale_midi_notes, semitone_pattern, registrations/lists).
- chords.py: Chord to WAV (chords_to_wav, play_arpeggio).
- counterpoint.py: Note translation (translate_in_scale, note_names, multi_note_names).
- scores.py: Score creation/manipulation (mk_score, ensure_part_filter, resolve_format_from_filepath, filter_parts, delete_parts).

## Key Functions/Classes
- def scale_midi_notes(scale: str, midi_range: tuple[int, int]) -> tuple[int]: 
  """Converts scale specs to MIDI notes. e.g., scale_midi_notes('C major', (60, 72)) -> (60, 62, 64, 65, 67, 69, 71, 72)"""
  Params: scale (e.g., 'C major'), midi_range (start/end MIDI). Returns: tuple of notes.

- def semitone_pattern(quality: str) -> tuple[int]: 
  """Get semitone intervals for scale quality. e.g., semitone_pattern('blues') -> (0, 3, 5, 6, 7, 10)"""
  Params: quality (e.g., 'major', 'blues'). Returns: interval tuple.

- def scale_params(scale_string: str) -> tuple[str, str]: 
  """Parse scale into root/quality. e.g., scale_params('F# harmonic minor') -> ('F#', 'harmonic minor')"""
  Params: scale_string. Returns: (root, quality).

- def register_scale_quality(name: str, pattern: tuple[int]): Registers custom scale.
- def list_scale_qualities() -> list[str]: Lists available scales (e.g., len ~ dozens).

- def chords_to_wav(chord_sequence: list[tuple[str, int] | str], name: str = '', render_chord=func) -> str: 
  """Generate WAV from chord sequence. e.g., chords_to_wav([('Bdim', 120), 'G7']) -> filepath"""
  Params: sequence (chord/dur or str), name (file prefix), render_chord (e.g., play_arpeggio). Returns: WAV path. Uses hum.Sound for display.

- def translate_in_scale(notes: list[str] | list[list[str]], steps: int, scale: str) -> music21.stream.Stream: 
  """Translate notes/stacks in scale. e.g., translate_in_scale(['C4', 'E4'], -2, 'C') -> Stream with ['A3', 'C4']"""
  Params: notes (single/multi-track), steps, scale (e.g., 'C'). Returns: Stream.

- def note_names(stream: music21.stream.Stream) -> list[str]: Extract note names.
- def multi_note_names(tracks: list[list[str]]) -> list[list[str]]: For multi-tracks.

- def mk_score(tracks: list[list[str]]) -> music21.stream.Score: Create Score from note lists.
- def filter_parts(part_filter: int | list[int] | callable | None, score_input: str | music21.stream.Score, save_to_filepath: str = None) -> music21.stream.Score: 
  """Filter score parts by index/func. e.g., filter_parts([0,2], score) keeps parts 0/2."""
  Params: filter (int/list/callable/None=all), score (path/Score), save_path. Returns: Filtered Score.

- def delete_parts(part_idx: int | list[int], score_input: str | music21.stream.Score, save_to_filepath: str = None) -> music21.stream.Score: 
  """Delete parts by index. e.g., delete_parts(1, score) removes part 1."""

## Usage Tips
- Imports: from tonal.notes import *; from tonal import chords_to_wav; from tonal.counterpoint import translate_in_scale; from tonal.scores import filter_parts.
- Dependencies: music21 (for Stream/Score/Note), hum (optional for Sound display).
- Patterns: Use with hum for audio playback. Register custom scales for extension.
- Notes: Supports doctests for examples. MIDI range typically 0-127.

## Examples
from tonal.notes import scale_midi_notes
notes = scale_midi_notes('C major', (60, 72))  # (60, 62, ...)

from tonal import chords_to_wav
wav = chords_to_wav([('Em11', 120), 'G7'])  # Generates WAV

from tonal.counterpoint import translate_in_scale
translated = translate_in_scale([['C4', 'E4']], -2, 'C')  # A3, C4