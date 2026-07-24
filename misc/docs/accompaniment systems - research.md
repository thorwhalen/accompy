# Building Python Accompaniment Systems: A Complete Technical Guide

Modern chord-to-audio accompaniment in Python requires integrating **pattern-based MIDI generation**, **SoundFont synthesis**, and **real-time streaming architecture**. The field has matured significantly, with open-source tools like [MMA (Musical MIDI Accompaniment)](https://www.mellowood.ca/mma/) providing Band-in-a-Box-like functionality, [SCAMP](https://github.com/MarcTheSpark/scamp) enabling real-time ensemble management, and Google Magenta's [MusicVAE](https://github.com/magenta/magenta/tree/main/magenta/models/music_vae) offering neural pattern generation. For tokenization, [MidiTok](https://github.com/Natooz/MidiTok) has emerged as the standard library supporting **REMI, Compound Word, and 8+ other representations** optimized for transformer models. The critical path for a Python accompaniment package involves: chord parsing → pattern application with voice leading → MIDI generation → SoundFont rendering (via [pyFluidSynth](https://github.com/nwhitehead/pyfluidsynth)) or neural synthesis (via [MIDI-DDSP](https://github.com/magenta/midi-ddsp)).

---

## Transforming chord symbols into playable MIDI patterns

Pattern-based accompaniment transforms chord symbols (Am7, Cmaj7) into MIDI events through a pipeline: **chord parsing** extracts pitch classes, **voicing selection** determines octave placement and inversions, **pattern application** provides rhythmic structure, and **context-aware rendering** ensures smooth voice leading between chords.

The [pychord](https://pypi.org/project/pychord/) library handles chord parsing, converting symbols to constituent notes with support for extensions and inversions. For voice leading, Dmitri Tymoczko's [voice leading software](https://dmitri.mycpanel.princeton.edu/software.html) implements algorithms minimizing total voice motion while avoiding parallel fifths. The Python [harmonizer project](https://github.com/meagtan/harmonizer) uses dynamic Bayesian networks with the Viterbi algorithm to estimate optimal voice leading from training data.

**Pattern storage formats** vary by instrument. Drum patterns store **velocity values at 16th-note subdivisions** (e.g., Band-in-a-Box uses 16-value rows per bar per instrument). Bass patterns define **scale degrees relative to chord root** (1, 3, 5, 7) with rhythmic timing. Piano/guitar comping patterns combine voicing dictionaries with rhythm templates. The [Strudel voicing system](https://strudel.cc/understand/voicings/) demonstrates modern approaches to chord voicing in JavaScript that translate well to Python implementations.

For direct chord-to-MIDI conversion, [chords2midi](https://github.com/Miserlou/chords2midi) creates MIDI files from chord progressions, while [midigen](https://github.com/dbjohnson/midigen) adds automatic voice leading. The comprehensive [MMA library](https://www.mellowood.ca/mma/) (GPL, Python 2.7/3.x) contains over **1000 patterns** across jazz, rock, country, latin, blues, and waltz styles, supporting import of Band-in-a-Box and Yamaha style files.

---

## Drum, bass, and comping pattern datasets for training and rendering

The [Groove MIDI Dataset](https://magenta.tensorflow.org/datasets/groove) from Google Magenta provides **13.6 hours of professional drummer performances** across 1,150 MIDI files and 22,000 measures—the gold standard for expressive drum pattern training. Its expanded version, [E-GMD](https://magenta.tensorflow.org/datasets/e-gmd), includes 444 hours of audio across 43 drum kits. For isolated stems, [StemGMD](https://zenodo.org/records/7860223) separates individual drum components.

Commercial-quality free patterns include [Grooves From Mars](https://samplesfrommars.com/products/grooves-from-mars) (478 templates from 27 drum machines) and [muted.io drum patterns](https://muted.io/drum-patterns/) for basic styles with MIDI download. The [jazznet dataset](https://github.com/tosiron/jazznet) offers **162,520 labeled piano patterns** including chords, arpeggios, scales, and progressions in all keys and inversions—~95GB total covering 26K+ hours.

For chord progressions with style metadata, the [McGill Billboard Dataset](https://github.com/boomerr1/The-McGill-Billboard-Project) contains **890 songs** from Billboard Hot 100 (1958-1991) with chord annotations, structure, and timing. The [Hooktheory API](https://www.hooktheory.com/api/trends/docs) provides 5000+ songs with chord transition probabilities and Roman numeral analysis. Jazz-specific resources include the [Jazz Harmony Treebank](https://github.com/DCMLab/JazzHarmonyTreebank) (hierarchical analyses from iRealPro) and [JAAH Dataset](https://mtg.github.io/JAAH/) (113 jazz tracks with aligned chord transcriptions).

---

## Commercial accompaniment tools reveal effective architectures

**Band-in-a-Box** uses a random pattern player rather than a sequencer—it selects from pattern pools for variation, applying music theory rules to determine correct note combinations for input chords. Style files (.STY) contain A/B patterns for verse/chorus, fills, intros, and endings. The [StyleMaker documentation](https://www.pgmusic.com/tutorial_stylemaker1.htm) and [full manual](https://www.pgmusic.com/manuals/bbw2022full/chapter14.htm) detail the pattern structure: 4 drum rows with pattern masking determining playback.

**iReal Pro** uses a URL-based chord chart format (`irealbook://Song=Artist=Style=Key=n=ChordProgression`) with 51 accompaniment styles. The [custom chart protocol](https://www.irealpro.com/ireal-pro-custom-chord-chart-protocol) and [chord symbols reference](https://technimo.helpshift.com/hc/en/3-ireal-pro/faq/88-chord-symbols-used-in-ireal-pro/) document the format. Over 1400 jazz standards are available in JSON format via [this repository](https://github.com/mikeoliphant/JazzStandards).

**Yamaha style files** are MIDI Format 0 files with additional non-MIDI chunks: CASM (channel assignment), OTS (one-touch settings), and MDB (metadata). The [comprehensive format documentation](http://www.jososoft.dk/yamaha/articles/style2_0.htm) covers both SFF1 and SFF2 (2008+) variants. JJazzLab provides [Yamaha style integration](https://jjazzlab.gitbook.io/user-guide/rhythm-engines/yamjjazz-rhythm-engine/yamaha-styles) for its open-source accompaniment system.

---

## Python libraries form the accompaniment generation stack

Core MIDI generation relies on three libraries: [MIDIUtil](https://github.com/MarkCWirt/MIDIUtil) (pure Python file creation), [pretty_midi](https://github.com/craffel/pretty-midi) (analysis and manipulation with [documentation](https://craffel.github.io/pretty-midi/)), and [mido](https://github.com/mido/mido) (low-level I/O with [real-time support](https://mido.readthedocs.io/)). For music theory operations, [music21](https://pypi.org/project/music21/) from MIT provides comprehensive chord, scale, and voice leading analysis.

Specialized accompaniment libraries include [expremigen](https://github.com/shimpe/expremigen) for expressive MIDI generation with animation support, [python-music-gen](https://github.com/pruperting/python-music-gen) for generating patterns from numbers and arpeggios, and [musicautobot](https://github.com/bearpelican/musicautobot) for deep learning MIDI generation with fast.ai. The [BandInMuseScore](https://berteh.github.io/BandInMuseScore/) plugin demonstrates MMA integration into notation software.

For AI-driven pattern generation, Google Magenta offers [MusicVAE](https://github.com/magenta/magenta/blob/main/magenta/models/music_vae/README.md) (variational autoencoder for melodies, drums, trios), [GrooVAE](https://magenta.tensorflow.org/groovae) (drum humanization and groove transfer), and [MelodyRNN](https://github.com/magenta/magenta/blob/main/magenta/models/melody_rnn/README.md) (LSTM melody generation). [Magenta Studio](https://magenta.withgoogle.com/studio/) packages these as Ableton plugins with Continue, Generate, Interpolate, Groove, and Drumify functions.

---

## SoundFonts and synthesis options for MIDI-to-audio rendering

The SoundFont ecosystem offers several high-quality free options. **FluidR3 GM** (~141MB, MIT license) serves as the standard default, available from [MuseScore](http://www.musescore.org/download/fluid-soundfont.tar.gz). **MuseScore_General** (35.9MB .sf3 / 208MB .sf2) provides MuseScore 2.2+ compatibility. **Timbres of Heaven** (~369MB) delivers expressive orchestral sounds with GS/XG compatibility and 259+ instruments—[available on Polyphone](https://www.polyphone.io/en/soundfonts/instrument-sets/261-timbres-of-heaven-v3-4-final). For lightweight deployment, **GeneralUser GS** (~32MB) from [schristiancollins.com](http://www.schristiancollins.com/generaluser.php) works well.

Major SoundFont repositories include [Musical Artifacts](https://musical-artifacts.com/artifacts?formats=sf2) (800+ SF2 files), the [Internet Archive collection](https://archive.org/details/500-soundfonts-full-gm-sets) (500+ GM sets), [SynthFont links directory](http://www.synthfont.com/links_to_soundfonts.html), and [Polyphone](https://www.polyphone.io/en/soundfonts). Instrument-specific options: **Salamander Grand Piano** and **Keppy's Steinway** for piano, TR-808/909 collections for drums.

For Python synthesis, [pyFluidSynth](https://github.com/nwhitehead/pyfluidsynth) provides full FluidSynth bindings with sequencer support and direct audio generation—it supports real-time note on/off, program changes, and effects (chorus, reverb). The simpler [midi2audio](https://github.com/bzamecnik/midi2audio) wraps FluidSynth for one-line batch conversion: `FluidSynth('soundfont.sf2').midi_to_audio('input.mid', 'output.wav')`. [pretty_midi](https://github.com/craffel/pretty-midi) offers both sine wave synthesis (`.synthesize()`) and FluidSynth rendering (`.fluidsynth()`).

---

## Humanization makes MIDI playback sound natural

Humanization involves **timing variations** (±5-20ms from grid), **velocity curves** (±10-20 units), **duration offsets** (±5-15%), and **swing** (50-70% delay on off-beats). The [midihum](https://github.com/erwald/midihum) library uses ML-based gradient boosted trees trained on 2,600 piano performances with ~400 features—the [detailed blog post](https://www.erichgrunewald.com/posts/introducing-midihum-an-ml-based-midi-humanizing-tool/) explains the approach. [MIDI-Humanizer](https://github.com/L0wl/midi-humanizer) provides a GUI tool with PySide6 for time/velocity/duration offsets.

For groove templates, Magenta's [GrooVAE](https://arxiv.org/abs/1905.06118) applies learned human timing patterns to quantized drums using a variational autoencoder. Simple algorithmic humanization can be implemented with mido by adding random offsets to note_on/note_off messages' delta times and velocities. Swing implementation shifts off-beat 8th notes by a configurable percentage of the eighth-note duration.

Neural approaches include [Performance RNN](https://github.com/magenta/magenta/tree/main/magenta/models/performance_rnn) which models expressive timing and dynamics with 128 note-on events, 128 note-off events, 100 time-shifts (10ms increments), and 32 velocity bins. Pre-trained models include `performance_with_dynamics` and `density_conditioned_model_with_dynamics` for controllable output.

---

## Neural audio synthesis offers realistic instrument rendering

[MIDI-DDSP](https://github.com/magenta/midi-ddsp) provides hierarchical MIDI-to-audio synthesis using Differentiable Digital Signal Processing. It works at three levels: note-level (MIDI input), performance-level (expression generator predicts vibrato, brightness, attack), and synthesis-level (DDSP additive + subtractive synthesis). Installation is straightforward: `pip install midi-ddsp` followed by `midi_ddsp_synthesize --midi_path input.mid`. It supports **13 instruments** from the URMP dataset: violin, viola, cello, double bass, flute, oboe, clarinet, saxophone, bassoon, trumpet, horn, trombone, and tuba.

The core [DDSP library](https://magenta.tensorflow.org/ddsp) enables training custom instrument models with ~10-20 minutes of monophonic audio. [DDSP-VST](https://github.com/magenta/ddsp-vst) packages this as real-time AU/VST3 plugins. For piano specifically, [ddsp-piano](https://github.com/lrenault/ddsp-piano) provides MAESTRO-trained synthesis. The foundational papers include [DDSP: Differentiable Digital Signal Processing](https://arxiv.org/abs/2001.04643) and [MIDI-DDSP: Detailed Control of Musical Performance](https://midi-ddsp.github.io/) (ISMIR 2022).

Beyond DDSP, [Magenta's wave2midi2wave](https://magenta.tensorflow.org/maestro-wave2midi2wave) combines piano transcription with synthesis, and emerging models like [SingSong](https://arxiv.org/abs/2301.12662) generate musical accompaniments directly from singing input.

---

## Music representations beyond MIDI suit different use cases

**MusicXML** preserves score-level details MIDI loses: enharmonic spelling (C# vs Db), staff notation elements, dynamics, and articulations. [music21](https://pypi.org/project/music21/) provides comprehensive MusicXML support for Python, enabling chord symbol analysis, Roman numeral extraction, and theory-aware manipulation. Use MusicXML when chord symbols, harmonic analysis, or notation-accurate pattern storage matter.

**Google Magenta's NoteSequence** is a Protocol Buffer format designed for ML pipelines, stored in TFRecord files. The [note-seq](https://github.com/magenta/note-seq) library (`pip install note-seq`) handles conversion from MIDI, quantization, and integration with Magenta models. NoteSequence excels for training MusicVAE, MelodyRNN, and other Magenta architectures.

**ABC Notation** is extremely compact and human-readable—ideal for LLM-based music generation. Recent research ([MuPT paper](https://arxiv.org/abs/2404.06393)) found LLMs inherently more compatible with ABC than MIDI, leading to SMT-ABC (Synchronized Multi-Track ABC) for multi-track generation. Python tools include [pyabc](https://github.com/campagnola/pyabc) for parsing, [abctool](https://github.com/a773music/abctool) for manipulation, and abc2midi for MIDI conversion. The [Nottingham Database](https://abc.sourceforge.net/NMD/) provides 1,200 folk tunes in ABC format.

---

## Token-based representations power transformer models

**REMI** (REvamped MIDI-derived events) from the [Pop Music Transformer paper](https://arxiv.org/abs/2002.00212) introduces Bar and Position tokens that provide metrical context—models can "count the beats." Token types include bar indicators, position within bar (0-15 for 16th notes), pitch, velocity, duration, tempo, and chord symbols. The [reference implementation](https://github.com/YatingMusic/remi) demonstrates the approach.

**Compound Word (CP)** representation from the [Compound Word Transformer](https://cdn.aaai.org/ojs/16091/16091-13-19585-1-2-20210518.pdf) (AAAI 2021) predicts multiple tokens simultaneously (pitch, duration, velocity), reducing sequence length by ~3x compared to REMI.

[MidiTok](https://github.com/Natooz/MidiTok) (`pip install miditok`) has emerged as the standard tokenization library, supporting **REMI, REMI+, CP, TSD, MIDI-Like, Octuple, MMM, PerTok, MuMIDI, and Structured** formats. It integrates BPE training and symusic for efficient processing. The [documentation](https://miditok.readthedocs.io/) provides comprehensive usage examples.

For accompaniment specifically: use **MusicXML + music21** for theory-aware generation, **NoteSequence** for Magenta models, **ABC** for LLM approaches, and **REMI/CP via MidiTok** for transformer architectures. REMI offers the best balance of metrical awareness and ecosystem support for chord-conditioned generation.

---

## Real-time architecture requires careful latency management

Real-time accompaniment systems use event-driven callbacks for chord input, separate threads for audio generation, and pre-allocated buffers. The recommended architecture: Input Handler Thread (receives MIDI/OSC via callbacks) → Scheduler/Clock Thread (manages beat-based timing) → Audio/MIDI Output Thread (low-latency synthesis) → Shared State Manager (thread-safe chord state).

**Latency budgets** vary by application: professional production requires **<10ms**, live performance with in-ear monitors **<15-20ms**, and live with floor monitors **<20-30ms**. Human perception thresholds: <3ms imperceptible, 3-10ms natural, 10-15ms sluggish, >30ms severely impacted. Buffer size directly determines latency: at 44.1kHz, 64 samples = 1.5ms, 128 samples = 2.9ms, 256 samples = 5.8ms.

The Python GIL causes unpredictable latency in threaded audio. Solutions include using C-implemented callbacks (as in [python-rtmixer](https://github.com/spatialaudio/python-rtmixer)) that don't invoke the Python interpreter, pre-allocating all buffers, and avoiding object creation in audio callbacks. [python-sounddevice](https://github.com/spatialaudio/python-sounddevice) with WDM-KS drivers achieves **1-1.5ms latency** (measured with oscilloscope).

---

## MIDI and audio libraries for real-time Python applications

[python-rtmidi](https://github.com/SpotlightKid/python-rtmidi) provides low-level MIDI I/O with **<5ms latency** for serial bridges, supporting ALSA, JACK, CoreMIDI, and Windows MultiMedia. Callback-based input enables real-time response without polling. [mido](https://github.com/mido/mido) offers a higher-level API using python-rtmidi as backend, with [comprehensive documentation](https://mido.readthedocs.io/).

For audio synthesis, [pyo](https://github.com/belangeo/pyo) delivers a full DSP toolkit written in C with OSC/MIDI support—it achieves ~1ms latency on Bela platform. [pyFluidSynth](https://github.com/nwhitehead/pyfluidsynth) enables real-time SoundFont playback and can generate audio samples directly via `get_samples()`. [python-sounddevice](https://github.com/spatialaudio/python-sounddevice) handles audio I/O with configurable latency settings.

**[SCAMP](https://github.com/MarcTheSpark/scamp)** (Suite for Computer-Assisted Music in Python) integrates these components with sophisticated clock management, FluidSynth integration, and MIDI/OSC I/O. It handles polyphonic tempo control and exports to MusicXML/LilyPond. The [thesis documentation](https://marcevanstein.com/Writings/Evanstein_MAT_Thesis_SCAMP.pdf) provides detailed architecture information.

Real-time chord detection can use [chordy](https://github.com/arulandu/chordy) (multi-threaded, ~6.7ms latency) or [autochord](https://pypi.org/project/autochord/) (Bi-LSTM-CRF, 67% accuracy on 25 chord classes).

---

## Open-source accompaniment systems provide implementation references

[Impro-Visor](https://github.com/Impro-Visor/Impro-Visor) is a Java-based jazz improvisation advisor with auto-generated accompaniment from chord progressions, LSTM neural network improvisation (v9.0+), and grammar-based lick generation. [Microsoft Muzic](https://github.com/microsoft/muzic) offers a comprehensive collection including **PopMAG** (accompaniment generation, ACM MM 2020), **GETMusic** (unified multi-track generation), and **MuseFormer** (fine/coarse-grained attention transformer).

[MuseGAN](https://github.com/salu133445/musegan) generates multi-track polyphonic music (bass, drums, guitar, piano, strings) using GANs. [ACE-Step](https://github.com/ace-step/ACE-Step) provides StemGen for instrument stem generation with controllable LoRA. The [automatic-music-accompaniment](https://github.com/cheriell/automatic-music-accompaniment) project demonstrates LSTM-based accompaniment prediction from melody.

For emotion-aware generation, [Emotion-Guided Piano Accompaniment](https://github.com/Duoluoluos/Emotion-Guided-Piano-Accompaniment-Generation) implements VAE-based generation with valence/arousal control. Sony CSL's [bass accompaniment demo](https://sonycslparis.github.io/bass_accompaniment_demo/) showcases latent diffusion for bass generation.

---

## Academic literature advances accompaniment generation

Foundational transformer work includes the [Music Transformer](https://arxiv.org/abs/1809.04281) (ICLR 2019) with relative attention for long-range dependencies, and the [Anticipatory Music Transformer](https://arxiv.org/abs/2306.08620) (2023) with controllable infilling showing "similar musicality to human-composed accompaniments."

Accompaniment-specific papers include **SongDriver** (ACM MM 2022) with a two-phase Transformer + CRF system achieving zero latency, [Structured Multi-Track Accompaniment Arrangement](https://arxiv.org/abs/2310.16334) (2023) with two-stage lead sheet → piano → multi-track generation, and **AccoMontage** (ISMIR 2021-2022) for neuro-symbolic piano accompaniment from lead sheets.

Rhythm-focused work includes the [GrooVAE paper](https://arxiv.org/abs/1905.06118) on humanization and Sony CSL's **High-Level Control of Drum Track Generation** (2019). The survey [Motifs, Phrases, and Beyond](https://arxiv.org/html/2403.07995v1) (2024) comprehensively covers structure-aware generation approaches.

For books, **"Algorithmic Composition: Paradigms of Automated Music Generation"** by Gerhard Nierhaus ([Springer, 2009](https://link.springer.com/book/10.1007/978-3-211-75540-2)) covers Markov models, grammars, genetic algorithms, and neural networks. **"Hands-On Music Generation with Magenta"** ([GitHub](https://github.com/PacktPublishing/Hands-On-Music-Generation-with-Magenta)) provides practical deep learning implementation guidance.

---

## Datasets and research resources complete the toolkit

**Chord progression datasets** for training: [McGill Billboard](https://github.com/boomerr1/The-McGill-Billboard-Project) (890 pop songs), [Hooktheory](https://www.hooktheory.com/api/trends/docs) (5000+ songs with transition probabilities), [Jazz Harmony Treebank](https://github.com/DCMLab/JazzHarmonyTreebank) (hierarchical jazz analyses), and the [CHORDONOMICON](https://hf.co/papers/2410.22046) (666,000 song chord progressions).

**MIDI collections**: [Lakh MIDI Dataset](https://colinraffel.com/projects/lmd/) (176,581 files), [MAESTRO](https://magenta.tensorflow.org/datasets/maestro) (200+ hours of piano), [POP909](https://github.com/music-x-lab/POP909-Dataset) (909 pop songs with annotations), and [Discover MIDI](https://zenodo.org/records/18073512) (6.74M de-duplicated files—the largest collection). For MusicXML, [PDMX](https://github.com/pnlong/PDMX) provides 250K+ public domain scores.

**Research groups** advancing the field: [Google Magenta](https://github.com/magenta/magenta), [Sony CSL Paris](https://www.sonycsl.co.jp/en/projects/flow-machines-2/) (Flow Machines), [Microsoft Muzic](https://github.com/microsoft/muzic), Spotify's Creator Technology Research Lab, and academic labs at MIT, QMUL (C4DM), Georgia Tech, and IRCAM. Key conferences: ISMIR, ICMC, SMC, and NIME.

---

## Conclusion

Building a Python accompaniment system requires integrating multiple specialized components. For **pattern-based MIDI generation**, start with [pychord](https://pypi.org/project/pychord/) for chord parsing and [MMA](https://www.mellowood.ca/mma/) as a reference implementation with 1000+ patterns. For **synthesis**, [pyFluidSynth](https://github.com/nwhitehead/pyfluidsynth) with [MuseScore_General](https://musescore.org/en/handbook/2/soundfonts-and-sfz-files) SoundFont provides reliable rendering; [MIDI-DDSP](https://github.com/magenta/midi-ddsp) offers neural realism for supported instruments. For **tokenization** in transformer models, [MidiTok](https://github.com/Natooz/MidiTok) with REMI encoding balances metrical awareness and ecosystem support. For **real-time applications**, [SCAMP](https://github.com/MarcTheSpark/scamp) provides the most complete integrated solution, managing timing, FluidSynth, and MIDI I/O with proper thread architecture. Train custom models using [Groove MIDI Dataset](https://magenta.tensorflow.org/datasets/groove) for drums, [jazznet](https://github.com/tosiron/jazznet) for piano patterns, and [McGill Billboard](https://github.com/boomerr1/The-McGill-Billboard-Project) or [Hooktheory](https://www.hooktheory.com/api/trends/docs) for chord progressions.


---

---


# EXTRA: Deep dive into automatic musical accompaniment systems

Generating intelligent musical accompaniment requires solving interconnected challenges: voice leading that avoids parallel fifths while minimizing motion, bass lines that anticipate harmonic destinations, humanization that captures the subtle imperfections of real performers, and architectures capable of real-time response. This continuation explores these areas with algorithm implementations, format specifications, AI approaches, and practical Python patterns.

## Voice leading and bass line generation with memory

The foundation of context-aware accompaniment lies in **Dmitri Tymoczko's geometric theory of voice leading**, where chords occupy points in n-dimensional orbifold space and voice leadings become line segments whose length measures total voice motion in semitones. The optimal algorithm generates all permutation mappings between two chords, calculates cumulative semitone motion, filters candidates containing parallel fifths or octaves, then selects the minimum-distance survivor.

**music21** (https://github.com/cuthbertLab/music21) implements voice leading analysis through its `VoiceLeadingQuartet` class, which detects parallel motion, hidden fifths, and voice crossing between any pair of voices. The library's methods—`parallelFifth()`, `parallelOctave()`, `hiddenFifth()`, `motionType()`—enable rule checking during voicing selection. Tymoczko himself provides Python tools at https://dmitri.mycpanel.princeton.edu/software.html including a voice-leading calculator and Tonnetz visualizer built on music21.

**Walking bass generation** follows contour-based rules codified in academic work by Dias and Guedes (2013): root on beat 1, fifth on beat 3, chord tones filling beat 2 based on motion direction, and chromatic approach notes on beat 4 targeting the next chord's root. The algorithm at https://github.com/MaxHilsdorf/Walking-Bass-Generator implements this pattern, selecting approach notes a semitone above or below the target. HMM-based approaches (Shiga & Kitahara, 2021) learn style-specific note distributions at each metric position from corpus data.

Implementing **memory for context-aware rendering** requires tracking voicing history, rhythm patterns, and register selections in a sliding window:

```python
class AccompanimentMemory:
    def __init__(self, history_length=8):
        self.voicing_history = deque(maxlen=history_length)
        self.rhythm_history = deque(maxlen=history_length)

    def score_candidate(self, voicing, rhythm):
        repetition_penalty = sum(
            1 for v in self.voicing_history if self.similar(v, voicing)
        )
        voice_leading_cost = self.vl_distance(self.voicing_history[-1], voicing)
        return 10 - repetition_penalty - (voice_leading_cost / 12)
```

The **mingus library** (https://github.com/bspaans/python-mingus, `pip install mingus`) provides chord generation, inversions, and recognition functions (`chords.major_triad()`, `first_inversion()`, `determine()`) useful for voicing candidate generation.

## MMA pattern format deconstructs groove creation

**MMA (Musical MIDI Accompaniment)** by Bob van der Poel (https://www.mellowood.ca/mma/) is a free, GPL-licensed Python program that compiles text files describing chord progressions and style directives into MIDI. The pattern definition syntax separates rhythm specification from harmonic content.

A **groove** combines track-specific patterns—Drum, Bass, Chord, Walk, Arpeggio, Plectrum—each with its own definition syntax. Drum patterns specify `Position Duration Volume` (e.g., `D1 1 0 90; 2 0 80; 3 0 90; 4 0 80` for quarter-note hits). Bass patterns add a note offset parameter (`1 4 1 90` means beat 1, quarter note, root, velocity 90). Chord patterns define voicing attacks. Duration notation uses `4` for quarter, `8` for eighth, `81`/`82` for swing eighths, and `+` or `.` for dotted values.

Voicing control uses `Chord Voicing Mode=Optimal Range=12 Center=4`, which minimizes voice leading distance while clustering notes around a specified center. MMA's `DefGroove` directive names a configured pattern set for reuse. The **800+ included grooves** span jazz, rock, Latin, and pop styles.

**Python integration** works via subprocess calls to the `mma` command-line tool or by forking the source (https://github.com/infojunkie/mma) for direct module import. The MuseScore plugin **BandInMuseScore** (https://github.com/berteh/BandInMuseScore) generates MMA files from notation. Compared to Band-in-a-Box's probabilistic pattern selection and RealTracks audio, MMA offers full source access and text-file version control at the cost of GUI polish and audio quality.

## Yamaha, Band-in-a-Box, and Roland style file internals

**Yamaha style files** (.sty) contain a mandatory Type 0 MIDI section followed by optional CASM, OTS, and MDB sections identified by magic bytes (`MThd`, `CASM`, `OTSc`, `FNRc`). The MIDI section uses markers like `Intro A`, `Main B`, `Fill In AA`, `Ending C` to delimit style parts across 8 channels: channel 10 for drums, 11 for bass, 12-13 for chords, 14 for pads, 15-16 for phrase parts.

The **CASM section** controls chord transposition behavior through **Ctab** structures specifying NTR (Note Transposition Rule: root-transposed vs. root-fixed) and NTT (Note Transposition Table: bypass, melody, chord, bass modes). SFF2 format (2008+) adds **Ctb2** for split note ranges with independent transposition rules per range. The definitive specification lives in Peter Wierzba's **StyleFileDescription_v21.pdf** (55 pages) at https://wierzba.hier-im-netz.de/StyleFileDescription_v21.pdf.

**sff2-tools** (https://github.com/bures/sff2-tools) parses Yamaha styles to YAML and back, enabling programmatic pattern extraction:

```python
# Extract MIDI section from Yamaha style
with open("style.sty", "rb") as f:
    data = f.read()
midi_start = data.find(b"MThd")
casm_pos = data.find(b"CASM")
midi_data = data[midi_start : casm_pos if casm_pos > 0 else len(data)]
```

**Band-in-a-Box** uses a completely different proprietary format (RIFF-based, magic bytes `52 49 46 46` followed by `.DMSTstyh`) with probabilistic pattern pools rather than fixed arrangements. Pattern weights (1-9) control selection probability. Conversion typically requires exporting to MIDI via BIAB itself.

**Roland .STL files** lack official documentation; reverse engineering (Peter Jazz blog) reveals headers starting with `G8<name>` markers and relative snippet pointers. The format is described as "spaghetti" due to missing explicit size fields.

## LLMs generate patterns through tokenization and prompting

**MIDI-LLM** (arXiv:2511.03942, November 2025) expands LLaMA's vocabulary with ~55,000 MIDI tokens, achieving **5-10x faster inference** than prior models through joint text-MIDI representation. Training combines continued pretraining on MusicPile (4B tokens of ABC notation, theory Q&A, scores) with supervised finetuning on text-MIDI pairs.

**MidiTok** (https://github.com/Natooz/MidiTok, `pip install miditok`) provides the standard tokenization schemes: **REMI** (bar+position tokens), **MIDILike** (note-on/off/time-shift), **TSD** (explicit durations), **Octuple** (multi-attribute), and **Compound Word** (embedding pooling for efficiency). REMI originated with Pop Music Transformer (Huang & Yang, 2020) and remains the most common choice.

**ABC notation** offers the highest compression for LLM music generation—ChatMusician (https://huggingface.co/m-a-p/ChatMusician, arXiv:2402.16153) achieves competitive symbolic generation using standard LLM tokenizers on ABC text. Effective prompts specify chord progressions explicitly: "Develop a musical piece using the given chord progression: 'Am', 'F', 'C', 'G'". The **Irish music bias** in training data requires explicit genre specification for other styles.

**Text-to-audio models** operate differently: **MusicGen** (https://github.com/facebookresearch/audiocraft) uses a single autoregressive transformer over EnCodec tokens with novel interleaving patterns, while **MusicLM** employs hierarchical sequence-to-sequence modeling with MuLan embeddings. **Riffusion** fine-tunes Stable Diffusion on spectrograms for real-time generation. For accompaniment specifically, the **Anticipatory Music Transformer** (Stanford CRFM, arXiv:2306.08620) enables infilling—generating accompaniment given melody—through arrival-time tokenization and anticipation controls.

## Humanization algorithms capture performer imperfection

**Timing humanization** centers on Gaussian jitter with σ = 5-15ms, but **groove templates** extracted from real performances explain more variance. The algorithm captures average timing deviation at each metric position, then applies the template with controllable strength:

```python
def apply_groove_template(note, template, strength=0.8):
    position = note.quantized_position % len(template)
    return note.time + (template[position] * strength)
```

Research (Wright & Berdahl, CCRMA 2006) found groove templates alone explain ~30% of microtiming variance, rising to ~39% with per-instrument templates. **Asymmetric perception** means early timing shifts sound worse than late ones; snare deviations are perceived more negatively than kick deviations.

**Swing quantization** delays every even-numbered 16th note by a factor proportional to swing percentage. MPC-style swing at 66% moves the second 8th note 1/3 of a 16th note late, creating triplet feel. The formula: `delay = (swing_percentage - 50) / 50 * (beat_duration / 4)`.

**Drum humanization** requires special attention: ghost notes at velocity 10-22 placed a 16th note before main hits, flams with 30ms grace note offsets, hi-hat openness variation (MIDI notes 42 vs 46), and **foot fatigue simulation** that reduces kick velocity over sustained passages. The **Groove MIDI Dataset** (https://magenta.withgoogle.com/datasets/groove) provides 13.6 hours of professional drummer performances for template extraction, while **GrooVAE** (Magenta) learns joint velocity/timing distributions in a VAE framework.

**DrumGizmo** (https://drumgizmo.org) implements production-grade humanization with parameters for laidback (-100 to +100ms), tightness, velocity attack/release, and standard deviation controls.

## Pattern datasets span drums, bass, piano, and multi-track

The **Lakh MIDI Dataset** (https://colinraffel.com/projects/lmd/) contains **176,581 MIDI files** under CC-BY 4.0, with the Clean MIDI subset (~17,000 files) organized by artist. Derived datasets include **Lakh Pianoroll** (174,154 multitrack piano rolls) and **Slakh2100** (2,100 files rendered with professional virtual instruments).

**Groove MIDI Dataset** (https://magenta.withgoogle.com/datasets/groove) offers **13.6 hours of expressive drumming** from 10 professionals with genre annotations (jazz, Brazilian, rock), tempo metadata, and hi-hat pedal control data. **E-GMD** expands this to 444 hours across 43 drum kits including 808, 909, and acoustic sets.

**JazzNet** (https://github.com/tosiron/jazznet) provides **162,520 labeled piano patterns** covering chords (dyads through tetrads), arpeggios, scales, and progressions (ii-V-I) in all inversions and keys. **Jazzify** (https://github.com/lucainiaoge/jazzify) implements walking bass and rootless voicing generation with swingified/bossaified pattern variants.

Free drum patterns come from **Groove Monkee** (https://groovemonkee.com/pages/free-midi-loops), **Prosonic Studios** (https://www.prosonic-studios.com/midi-drum-beats), and **Muted.io** (https://muted.io/drum-patterns/). Bass patterns from Groove Monkee include matching funk, jazz walk, and blues sets with chord progressions.

For dataset creation, **mirdata** (https://github.com/mir-dataset-loaders/mirdata) provides unified Python loaders, while **pretty_midi** enables extraction, quantization, and segmentation pipelines.

## Diffusion models enable chord-conditioned accompaniment

**Polyffusion** (https://github.com/aik2mlj/polyffusion, arXiv:2307.10304) represents the state-of-the-art for **chord-conditioned accompaniment generation**. It uses piano roll image representation with a U-Net backbone, supporting both internal control (masked infilling) and external control (cross-attention with encoded chords/textures). Tasks include melody generation given accompaniment, **accompaniment generation given melody**, and arbitrary segment inpainting.

**Symbolic Music Diffusion** (https://github.com/magenta/symbolic-music-diffusion, arXiv:2103.16091) established the VAE+diffusion paradigm: pre-trained MusicVAE embeds 64-bar phrases into continuous latent codes, then diffusion learns to denoise Gaussian noise into valid sequences. The approach enables parallel, non-autoregressive generation.

**Multi-Track MusicLDM** (arXiv:2409.02845) extends latent diffusion to arrangement generation—generating any subset of tracks given others. **Stochastic Control Guidance** (arXiv:2402.14285) enables training-free chord conditioning through non-differentiable rule guidance, working plug-and-play with pre-trained models.

For real-time generation, **AudioLCM** (arXiv:2406.00356) achieves **333x faster than real-time** through consistency distillation, reducing diffusion steps from hundreds to just 2. **Stable Audio Open** (https://huggingface.co/stabilityai/stable-audio-open-1.0) generates 47 seconds of stereo audio in under 1 second on A100.

Diffusion models excel at infilling and fine-grained control but require more compute than autoregressive transformers. **MusicGen** offers better local coherence and faster inference; diffusion provides more diverse outputs and natural masking. Hybrid approaches like JEN-1 combine omnidirectional diffusion with LM conditioning.

## Python real-time architecture balances precision with practicality

**python-rtmidi** (https://github.com/SpotlightKid/python-rtmidi) provides cross-platform MIDI I/O with callback-based input and virtual port creation. **mido** (https://github.com/mido/mido) offers higher-level MIDI object manipulation. **isobar** (https://ideoforms.github.io/isobar/) implements pattern-based sequencing with ~1ms timing precision at 120 BPM.

For **DAW integration**, create virtual ports via **loopMIDI** (https://www.tobias-erichsen.de/software/loopmidi.html) on Windows or enable IAC Driver on macOS, then configure the DAW to receive from the virtual port:

```python
import rtmidi

midi_out = rtmidi.MidiOut()
midi_out.open_virtual_port("Python Accompaniment")
# DAW sees "Python Accompaniment" as MIDI input
```

**Spotify's Pedalboard** (https://github.com/spotify/pedalboard) enables VST3/AU hosting from Python, loading instruments and effects for audio rendering. However, Python's **GIL and garbage collection** make sub-millisecond timing unreliable—use 1024+ sample buffers and minimize object allocation in audio callbacks.

**aiotone** (https://github.com/ambv/aiotone) demonstrates AsyncIO-based MIDI sequencing achieving 8+ voice polyphony without underruns. For beat detection, **aubio** provides real-time tempo tracking via `aubio.tempo()`.

**OSC integration** via **python-osc** (`pip install python-osc`) enables network control with higher timestamp precision than MIDI:

```python
from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.0.1", 5005)
client.send_message("/tempo", 120)
```

## Conclusion: assembling the accompaniment system

The path from chord symbols to musical accompaniment now has clear algorithmic foundations. Voice leading minimizes semitone motion while avoiding parallel motion through permutation search and rule filtering—music21 provides the analysis tools, mingus the chord generation. MMA offers an open, text-based pattern format with Python-native implementation, while Yamaha style files (via sff2-tools) unlock thousands of professionally-designed grooves.

AI approaches split between symbolic (MidiTok tokenization + transformers/diffusion) and audio (MusicGen, Stable Audio). For accompaniment specifically, **Polyffusion's chord-conditioned infilling** and the **Anticipatory Music Transformer's melody-to-accompaniment generation** represent the most directly applicable models. Humanization transforms mechanical patterns into believable performances through groove templates, Gaussian timing jitter, metric accents, and instrument-specific articulation rules.

The practical implementation combines python-rtmidi for MIDI I/O, virtual ports for DAW routing, state management for context tracking, and careful attention to Python's timing limitations. The 1ms precision achievable with isobar suffices for most musical applications when combined with large enough audio buffers. For production systems requiring tighter timing, the control logic remains in Python while audio-critical paths move to C/C++ extensions or external synthesis engines accessed via MIDI.