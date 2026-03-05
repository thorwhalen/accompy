"""
WIP modules for accompy - exploring chord-to-audio pipeline architecture.

The core idea: there are various *types* on the path from chords to audio,
and multiple *converters* between them. We make the types explicit and
organize the converters in a registry so they can be discovered and swapped.

Type pipeline::

    ChordSheet (text formats: ChordPro, iReal URL, plain text, MusicXML)
        |
        v
    ChordSequence (list of (chord_symbol, duration_beats) pairs)
        |
        v
    NoteSequence (list of (midi_notes, duration_beats) pairs - resolved chords)
        |
        v
    MidiData (MIDI file bytes or pretty_midi.PrettyMIDI object)
        |
        v
    AudioData (numpy array of audio samples or WAV bytes)

Each arrow is a converter function. Some converters skip steps
(e.g., chord_sheet -> audio directly via MusicGen-Chord).
"""
