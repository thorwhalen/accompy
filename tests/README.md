# accompy Test Suite

Comprehensive test suite for the accompy library.

## Test Coverage

### test_core.py (39 tests)
Tests for core functionality:

- **Chord Normalization** (7 tests)
  - Minor chord normalization (Cm → C-)
  - Major seventh normalization (Cmaj7 → C^7)
  - Diminished and half-diminished chords
  - Altered chords preservation
  - Slash chord handling

- **Chord String Parsing** (4 tests)
  - Bar line format parsing
  - Multiple chords per bar
  - Repeat symbols (%)
  - Space-separated format

- **Score Class** (4 tests)
  - Score creation from strings
  - Metadata handling
  - Iteration and length

- **Score Coercion** (6 tests)
  - From chord strings
  - From Score objects
  - From (chord, beats) tuples
  - From chord lists
  - From measures lists
  - Invalid input handling

- **Chord to MIDI Notes** (7 tests)
  - Major, minor, and seventh chords
  - Diminished chords
  - Chord with accidentals

- **MIDI Generation** (4 tests)
  - Builtin backend generation
  - Different styles
  - Different tempos
  - Multiple repeats

- **Audio Generation** (2 tests)
  - WAV generation (mocked)
  - Temp file creation

- **Configuration** (3 tests)
  - Default configuration
  - Custom configuration
  - Config with generate_accompaniment

- **Integration** (3 tests)
  - Complete workflows
  - Chord tuple workflow
  - Jazz progressions

### test_patterns.py (28 tests)
Tests for musical patterns:

- **Pattern Data Structures** (4 tests)
  - DrumHit creation and immutability
  - NoteEvent creation and immutability

- **Pattern Classes** (4 tests)
  - DrumPattern with tempo calculations
  - BassPattern creation
  - CompingPattern creation

- **Built-in Patterns** (6 tests)
  - Swing, bossa, rock, and waltz patterns
  - Pattern structure validation

- **Pattern Retrieval** (5 tests)
  - Get patterns by style
  - All styles available
  - Unknown style defaults

- **Pattern Validation** (4 tests)
  - MIDI velocities in range (0-127)
  - Beat positions non-negative
  - Note durations positive

- **MIDI Drum Notes** (2 tests)
  - Uniqueness
  - Valid MIDI range

- **Pattern Consistency** (2 tests)
  - Time signature consistency
  - All patterns have content

### test_audio_production.py (25 tests)
Tests specifically for audio production from chords:

- **Simple Chords to MIDI** (4 tests)
  - Single chord
  - Four-chord progression (I-vi-IV-V)
  - 12-bar blues
  - Jazz ii-V-I

- **MIDI Content Verification** (2 tests)
  - Multiple tracks in MIDI
  - Tempo metadata in MIDI

- **Different Styles** (8 tests)
  - Swing, bossa, rock, ballad, funk, latin, waltz, blues
  - File size validation
  - MIDI validity

- **Complex Chords** (3 tests)
  - Extended chords (9th, 11th, 13th)
  - Altered dominants
  - Slash chords (inversions)

- **Musical Parameters** (6 tests)
  - Various tempos (60-200 BPM)
  - Waltz time signature (3/4)

- **Complete Songs** (2 tests)
  - Verse-chorus structure
  - Autumn Leaves jazz standard

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_core.py -v
pytest tests/test_patterns.py -v
pytest tests/test_audio_production.py -v
```

Run specific test class:
```bash
pytest tests/test_core.py::TestChordNormalization -v
```

Run with coverage:
```bash
pytest tests/ --cov=accompy --cov-report=html
```

## Testing Audio Production

The test suite verifies audio production by:

1. **MIDI Generation**: Tests generate actual MIDI files and verify they are valid
2. **File Validation**: Checks MIDI header, track count, and file size
3. **Content Inspection**: Examines MIDI structure and metadata
4. **Style Variations**: Tests all 8 musical styles
5. **Musical Accuracy**: Tests chord parsing, time signatures, and tempos

### Example: Testing Simple Chords

```python
from accompy import generate_accompaniment

# Generate MIDI from simple chords
result = generate_accompaniment(
    "| C | Am | F | G |",
    style="rock",
    tempo=120,
    output_format="midi"
)

# Tests verify:
# - File is created
# - File is valid MIDI
# - Has expected tracks (drums, bass, piano)
# - Has correct tempo metadata
```

## Test Requirements

- pytest >= 7.0
- No FluidSynth required (tests generate MIDI only, mock audio rendering)
- All tests run in isolation with temporary directories

## Future Test Ideas

- MIDI event timing verification
- Chord voicing accuracy
- Pattern variation tests
- iReal Pro URL parsing tests
- MMA backend tests (when MMA is available)
