# Documentation Guide

Index of documents in `misc/docs/`. Read this first to decide which docs are relevant to your task.

## User-Facing Guides

| Document | Synopsis |
|----------|----------|
| [QUICK_START.md](QUICK_START.md) | 5-minute guide: install, setup (automated or manual), generate your first backing track. Start here for basic usage. |
| [SETUP.md](SETUP.md) | Detailed setup instructions: FluidSynth, SoundFont, MMA, Python deps. Troubleshooting for each platform. |
| [PATTERNS.md](PATTERNS.md) | How the builtin pattern system works: DrumPattern, BassPattern, CompingPattern dataclasses, how patterns map to MIDI events, how to create custom patterns. |
| [CHANGES.md](CHANGES.md) | Changelog for setup/UX improvements: automated setup wizard, diagnostics system, SoundFont management. |

## Architecture & Design

| Document | Synopsis |
|----------|----------|
| [architecture_v0.2.0.md](architecture_v0.2.0.md) | The v0.2.0 refactoring: before/after comparison, module responsibilities, protocol-based extensibility, registry pattern, event-based MIDI generation. Read this for understanding the current modular architecture. |
| [dev_plan_2026_01_05.md](dev_plan_2026_01_05.md) | Detailed 9-phase refactoring plan with specific instructions: decomposition, protocols, registry, chord resolution, synthesis, config, testing, cleanup, docs. Read this before doing any major refactoring. |
| [pipeline_architecture.md](pipeline_architecture.md) | The type-centric converter pipeline: 5 data types (ChordSheet → ChordSequence → NoteSequence → MidiData → AudioData), converter registry, backend selection. Read this for the `accompy.converters` / `accompy.pipeline` subsystem. |

## Tool & Ecosystem Research

| Document | Synopsis |
|----------|----------|
| [tool_notes.md](tool_notes.md) | Hands-on testing notes for pychord, pretty_midi, music21, mingus, mido, midiutil, tonal. API examples, gotchas, compatibility findings. Read this before integrating or debugging a music library. |
| [packages_summaries.md](packages_summaries.md) | Summaries of related packages in the ecosystem: tonal, hum, sung, theremin, arioso. Read this to understand how accompy fits with sibling packages. |
| [extra_resources.md](extra_resources.md) | Deep-dive research report on building Python accompaniment systems: pattern-based MIDI generation, SoundFont synthesis, real-time streaming, neural approaches. Covers MMA, SCAMP, MusicVAE, MidiTok, voice leading algorithms. |

## Research Papers & Reports

| Document | Synopsis |
|----------|----------|
| [accompaniment systems - research.md](accompaniment%20systems%20-%20research.md) | Survey of accompaniment tools and academic papers: iReal Pro ecosystem, comparison articles, pyRealParser, MusicXML converters, jazz education references. |
| [Automating chord progressions into realistic band recordings.md](Automating%20chord%20progressions%20into%20realistic%20band%20recordings.md) | 2025-2026 landscape report: MusicGen-Chord, MusiConGen, Anticipatory Music Transformer, Band-in-a-Box scripting (pybiab), MMA, DawDreamer VST rendering. Read this for AI/ML approaches to chord-conditioned audio generation. |
| [Programmatic MIDI Accompaniment Generation.md](Programmatic%20MIDI%20Accompaniment%20Generation.md) | Comprehensive academic-style evaluation of chord-to-MIDI architectures: ChordPro format, JSON schemas, real-time MIDI event streams, Yamaha Style Files, SysEx protocols, custom vs preset generation paradigms. |
