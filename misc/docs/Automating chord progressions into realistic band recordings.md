# Automating chord progressions into realistic band recordings

**The most viable path from chord sequences to realistic audio in 2025–2026 combines two breakthroughs: MusicGen-Chord (which directly generates audio from text chord symbols) and DawDreamer (which renders MIDI through professional VST instruments headlessly).** These tools, layered with open-source chord parsers and optional AI enhancement from Suno or Udio, can fully automate the pipeline the user currently performs manually. The field has matured rapidly — purpose-built chord-conditioned models now exist, commercial tools like Band-in-a-Box can be scripted via Python, and end-to-end open-source pipelines are achievable today. This report maps every relevant tool, library, API, and model across the full stack from chord notation to finished audio.

---

## Direct chord-to-audio AI models are now production-ready

Three AI systems stand out for accepting chord progressions as structured input and producing audio or MIDI output directly.

**MusicGen-Chord** (by developer sakemin) is the most immediately useful tool for this pipeline. It modifies Meta's MusicGen-Melody model by replacing one-hot melody chroma vectors with **multi-hot chord chroma vectors** — a clever hack that requires zero fine-tuning on the pretrained 1.5B-parameter weights. Input is remarkably simple: text chords like `C D:min G:7 C` (space-separated bars, comma-separated chords within bars), plus a BPM value, time signature, and a text prompt describing the desired genre (e.g., "smooth jazz trio" or "driving rock"). It supports **17 chord types** including major, minor, diminished, augmented, all sevenths, suspended, and sixth chords. Output is 32kHz audio up to 30 seconds per generation, chainable for longer pieces. Multi-Band Diffusion decoding reduces artifacts. It is available via **Replicate API** (`sakemin/musicgen-chord`), with a stereo variant (`sakemin/musicgen-stereo-chord`), and all code is on GitHub under Apache 2.0 (weights are CC-BY-NC 4.0).

**MusiConGen** (ISMIR 2024) builds on MusicGen-Melody with an "adaptive in-attention" conditioning mechanism and "jump finetuning" — training only the first self-attention layer in each Transformer block, making it trainable on consumer GPUs. It accepts symbolic chord progressions plus BPM and text prompts, with **explicit rhythm control** that MusicGen-Chord lacks. It was trained specifically on **5,000 backing track clips** from YouTube and outperforms baseline MusicGen on chord and rhythm adherence metrics. Available via GitHub, Replicate, and a Hugging Face Space (`fffiloni/MusiConGen`).

**Anticipatory Music Transformer** (Stanford CRFM, NeurIPS 2023) takes a different approach: it generates **symbolic MIDI**, not audio, using an "anticipation" mechanism that interleaves event sequences with control sequences. Its chord-conditioned variant accepts lead sheets (chord + melody) and generates multi-instrument accompaniment. Human evaluators rated its output as **comparable to human-composed accompaniments**. Models range from 128M to 780M parameters, all under Apache 2.0. It integrates with Ableton Live via a MIDI plugin for real-time co-composition. The catch: MIDI output requires external synthesis to become audio, but this is well-solved by downstream tools.

Other notable AI models include **AIVA**, which accepts chord progressions via its web UI and generates multi-layer compositions across 250+ styles, though its API requires a special licensing agreement. **ChatMusician** (a fine-tuned LLaMA-2) accepts chords in ABC notation for symbolic generation. Research models like **Chord-Conditioned Song Generator** (Interspeech 2024), **BandControlNet**, and **Chord-Transformer** show promising results but lack public releases. Google's MusicLM/MusicFX, Stable Audio, and OpenAI's Jukebox **do not accept chord input** — they are text-prompt or genre-conditioned only.

---

## Band-in-a-Box remains the gold standard for realism, and it can be scripted

**Band-in-a-Box** (PG Music) deserves special attention because its **RealTracks** technology uses actual recordings of session musicians — over 4,400 hours in version 2026 — dynamically reassembled to match any chord progression. The result is genuinely realistic-sounding band performances across jazz, blues, rock, pop, country, Latin, funk, and dozens of other genres. No AI model currently matches this level of instrument realism for full-band arrangements.

The critical finding for automation: while PG Music offers **no official API**, the open-source Python library **pybiab** (`github.com/cifkao/pybiab`, BSD-3-Clause) automates Band-in-a-Box and RealBand on Windows through GUI automation. It was used to generate the Groove2Groove MIDI Dataset at academic scale, proving batch processing is feasible. The workflow: programmatically load chord files, select styles, generate arrangements, and export WAV/MIDI in a loop. Band-in-a-Box 2026 also ships as a **VST2/VST3/AU DAW plugin**, opening scripting possibilities through DAW automation frameworks.

**MMA (Musical MIDI Accompaniment)** is the strongest fully open-source alternative — a Python-based program (GPL licensed) that reads a simple text DSL specifying chords and groove styles, then outputs multi-track MIDI files with realistic accompaniment patterns for drums, bass, piano, guitar, strings, and more. It includes hundreds of built-in grooves spanning jazz, blues, rock, Latin, bossa nova, swing, funk, and techno. Output MIDI can be rendered to audio via FluidSynth or DawDreamer. MMA is essentially a free, scriptable Band-in-a-Box for MIDI generation.

**iReal Pro** exports MIDI and audio (WAV/AAC) but has **no API and no scripting interface**. Its value in this pipeline is as a chord source — the iReal Pro community hosts thousands of chord charts that can be parsed programmatically using **pyRealParser** (`pip install pyRealParser`) or the JavaScript **ireal-reader** npm package. A separate tool, **ireal-musicxml** (GitHub: infojunkie), converts iReal Pro format directly to MusicXML.

---

## The programmatic chord-to-MIDI-to-audio toolkit is mature

Building a chord-to-audio pipeline from open-source components requires three layers: chord parsing, MIDI generation, and audio rendering. Each layer has strong tooling.

**For chord parsing and music theory**, the Python ecosystem offers excellent options. **pychord** (`pip install pychord`) parses standard chord symbols — `Chord("Cmaj7").components()` returns `['C', 'E', 'G', 'B']` — with support for inversions, slash chords, and custom quality definitions. **mingus** provides the deepest music theory: `chords.from_shorthand("Cm7")` resolves to note names, with built-in support for triads through thirteenths, suspended, altered, augmented, diminished, and polychords, plus a progressions module. **music21** (MIT) handles MusicXML, MIDI, ABC notation, and Humdrum kern, with `ChordSymbol` and `RomanNumeral` objects for harmonic analysis.

For **chord format parsing specifically**: pyRealParser handles iReal Pro URLs; pychopro and chordpro-parser handle ChordPro files; music21 reads MusicXML harmony elements (`<harmony>` with `<root>`, `<kind>`, `<bass>`, `<degree>`); pyabc and sjkabc parse ABC notation. The JavaScript library **ireal-musicxml** converts between iReal Pro and MusicXML. **music21 serves as a universal hub** — it reads nearly every format and can write MIDI, MusicXML, and LilyPond.

**For MIDI generation from chord data**, **pretty_midi** is the workhorse — create instruments, add notes with pitch/velocity/start/end, and write MIDI files. It pairs naturally with pychord (resolve chord names to notes) and includes built-in FluidSynth integration (`midi_data.fluidsynth(sf2_path='font.sf2')`). **chords2midi** provides a CLI shortcut: `c2m I V vi IV --key C --bpm 120` generates MIDI directly from Roman numerals or letter names, with voice leading, strumming patterns, and bassline generation built in. **mido** offers lower-level MIDI message construction for custom requirements.

**For rendering MIDI to audio**, three tiers exist:

- **FluidSynth** (via `pip install midi2audio`): the simplest path. `FluidSynth('font.sf2').midi_to_audio('input.mid', 'output.wav')` renders MIDI using SoundFont sample banks. Quality depends entirely on the SoundFont — FluidR3_GM is decent, Timbres of Heaven is better, and specialized SoundFonts (Salamander Grand Piano, SM Drums) can sound quite good. Realism rating in user studies: **~19%** compared to human recordings.
- **DawDreamer** (`pip install dawdreamer`): hosts VST2/VST3 instrument and effect plugins **headlessly from Python**. Load professional instruments like Kontakt, Pianoteq, or Spitfire libraries, feed MIDI, and render to NumPy arrays or WAV files in batch. Supports multi-track signal processing graphs, parameter automation, and Faust DSP integration. Works on macOS, Windows, Linux, and even Google Colab. This is the **best option for high-quality batch rendering** with deterministic output.
- **MIDI-DDSP** (Google Magenta, `pip install midi-ddsp`): neural synthesis that converts MIDI to realistic monophonic instrument audio (violin, flute, trumpet, cello) with automatically generated expression (vibrato, dynamics, articulation). Realism rating: **~56%**. Excellent for orchestral instruments but cannot handle polyphonic instruments like piano or full-band arrangements.

**Pedalboard** (Spotify, `pip install pedalboard`) completes the chain with studio-quality audio effects processing — reverb, compression, EQ, distortion, chorus, and VST3/AU effect plugin hosting — running up to 300x faster than pySoX.

---

## Suno and Udio can enhance basic tracks but cannot be directly chord-conditioned

The user's current workflow — rendering a backing track and feeding it to Suno — works because both **Suno and Udio accept audio uploads** as creative seeds, even though neither accepts chord progressions as structured input.

**Suno** (V4.5/V5) allows Pro/Premier users to upload up to 8 minutes of audio, which the system uses to inform key, BPM, and melodic shape for new generation. The "Cover" feature re-renders uploaded audio in a different style with controllable Weirdness, Style Influence, and Audio Influence sliders. Suno produces **44.1kHz audio** and can generate 90+ second songs in under 60 seconds. There is **no official API**, but the popular open-source project **gcui-art/suno-api** (GitHub, LGPL-3.0) reverse-engineers Suno's endpoints using browser cookie authentication with hCaptcha solving. Third-party commercial wrappers like sunoapi.org and AIMLAPI also exist.

**Udio** offers arguably higher audio fidelity — widely described as "studio quality" — and its audio conditioning approach is different: Udio **includes and merges** the uploaded audio with the extension, applying stem separation to isolate lead melodies and writing new arrangements around them. This means it tends to preserve the original harmonic content more faithfully than Suno. There is **no official public API**; the open-source **UdioWrapper** (`github.com/flowese/UdioWrapper`) provides Python access via reverse-engineered endpoints.

**MusicGen-Melody** (Meta) offers an open-source alternative for audio conditioning: upload a simple rendering of your chords (piano or guitar) as a "melody" reference, add a text prompt describing the desired style, and MusicGen will generate a full arrangement that follows the harmonic structure of the input. This works because MusicGen extracts a binarized chromagram from the reference audio — which captures chord information naturally. Available via the `audiocraft` Python library and Hugging Face, with models from 300M to 3.3B parameters.

**Stable Audio 2.5** (Stability AI) supports audio-to-audio transformation and inpainting at up to **48kHz/24-bit quality**, making it another option for enhancing basic MIDI renders. Its open-source training framework (`stable-audio-tools`) supports custom model training. However, it offers no structured chord input — only text prompts and audio conditioning.

---

## Chord notation formats and their conversion pathways

The five major chord notation formats each have parser libraries and conversion tools:

- **iReal Pro format**: URL-encoded proprietary notation with 16-cell row structure, chord symbols, bar lines, sections, repeats, and time signatures. Parsed by pyRealParser (Python) and ireal-reader (JavaScript). Converted to MusicXML via ireal-musicxml.
- **ChordPro** (`.cho`/`.chopro`): Text format with inline chords in brackets (`[Am]Hello [G]world`) and directives for title, key, tempo. Parsed by pychopro and chordpro-parser (Python). Can embed ABC notation.
- **MusicXML**: XML standard using `<harmony>` elements with `<root>`, `<kind>`, `<bass>`, and `<degree>` sub-elements. Full read/write in music21 and partitura.
- **ABC notation**: Compact text notation popular for folk music. Parsed by pyabc, sjkabc, and music21.
- **MIDI**: Not a chord format per se, but the universal interchange for note-level data. All tools above can output MIDI.

A universal conversion hub is possible through **music21**, which reads iReal Pro (via pyRealParser intermediary), MusicXML, MIDI, ABC, and Humdrum kern, and can output to any of these plus LilyPond for notation. For the chord-conditioned AI models specifically, the target format is simple text: MusicGen-Chord needs `C D:min G:7 C` and MusiConGen needs `C:maj,G:maj E:min,A:min` — both trivially generated from any parsed chord source.

---

## Four complete pipeline architectures from simplest to most powerful

**Pipeline 1 — Simplest (all open-source, ~10 lines of Python)**:
Parse chords with pyRealParser or pychord → generate MIDI with chords2midi or pretty_midi → render with FluidSynth + a quality SoundFont → output WAV. Quality: adequate for demos, not realistic enough for production.

**Pipeline 2 — AI direct (open-source, GPU required)**:
Parse chords → format as MusicGen-Chord text input → call via Replicate API or local inference with genre/BPM/time-signature parameters → receive 32kHz audio. Quality: good, with full-band arrangements. Limitation: 30-second chunks, CC-BY-NC license.

**Pipeline 3 — Professional VST (highest consistent quality)**:
Parse chords → generate multi-track MIDI arrangement via MMA (Musical MIDI Accompaniment) → render through DawDreamer hosting professional VST instruments → post-process with Pedalboard (reverb, compression, EQ) → output WAV. Quality: depends on VST libraries, potentially studio-grade. Fully deterministic and batchable.

**Pipeline 4 — Hybrid AI enhancement (best quality-to-effort ratio)**:
Parse chords → render basic audio (FluidSynth or simple piano MIDI) → feed as melody conditioning to MusicGen-Melody with style text prompt → or upload to Suno/Udio via unofficial API → receive professional-quality full arrangement. This most closely replicates the user's current manual workflow but automated end-to-end.

---

## Batch processing and API availability at a glance

| Tool | API/Automation | Batch-Ready | Chord Input |
|------|---------------|-------------|-------------|
| **MusicGen-Chord** | Replicate API, local Python | Yes | Direct text chords |
| **MusiConGen** | Replicate, local Python | Yes | Direct text chords |
| **Anticipatory Music Transformer** | Python library (`anticipation`) | Yes | MIDI events |
| **Band-in-a-Box** | pybiab GUI automation (Windows) | Yes (fragile) | Native chord symbols |
| **MMA** | Python CLI, fully scriptable | Yes | Text DSL |
| **DawDreamer** | Python library | Yes | MIDI files |
| **FluidSynth** | Python via midi2audio | Yes | MIDI files |
| **Suno** | Unofficial (gcui-art/suno-api) | Yes (risky) | Audio upload only |
| **Udio** | Unofficial (UdioWrapper) | Yes (risky) | Audio upload only |
| **AIVA** | By special agreement only | Limited | Web UI chords |
| **Beatoven.ai** | Official API + Python SDK | Yes | Text prompts only |
| **Loudly** | Official Music API | Yes | Genre/tempo/key only |
| **iReal Pro** | None | No | Native format |

Real-time capability exists in the Anticipatory Music Transformer (via Ableton plugin), Magenta's Improv RNN (in-browser via JavaScript), and RAVE (20x faster than real-time for timbre transfer). All other tools are batch-oriented, with generation times ranging from under 2 seconds (Stable Audio on H100) to several minutes (MusicGen on consumer GPU).

---

## Conclusion: a practical automation strategy

The user's ideal automated pipeline should combine **MusicGen-Chord or MusiConGen for direct chord-to-audio generation** as the primary path, with **MMA + DawDreamer** as a deterministic fallback for cases requiring precise arrangement control. The chord parsing layer (pyRealParser for iReal Pro, pychord for generic chord symbols, music21 for MusicXML) feeds into either path trivially. For maximum quality on the "real band" criterion, **Band-in-a-Box via pybiab** remains unmatched due to RealTracks — actual musician recordings reassembled to match chords — though it requires Windows and GUI automation. The Suno/Udio enhancement step can be retained in the automated pipeline via unofficial API wrappers, but this introduces fragility and potential terms-of-service concerns. The most robust, fully open-source, batchable pipeline today is: **pyRealParser → pychord → MMA → FluidSynth** for decent quality, or **pyRealParser → MusicGen-Chord via Replicate** for AI-generated audio that follows chord progressions with genre styling. Both can process hundreds of chord sequences unattended.