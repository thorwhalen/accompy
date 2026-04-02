"""
Rhythmic skeletons — duration-only measure patterns for simple accompaniment.

A rhythmic skeleton is a tuple of durations (in beats) that sum to the time
signature, describing when you strike within a measure and for how long each
strike sustains, with no regard for what you play. No pitches, no voicings, no
velocities, no instrument assignments.

The purpose of separating this layer out is to provide a gravitational center
for more sophisticated generation. A human accompanist doesn't mechanically
repeat a fixed pattern — they vary, anticipate, syncopate, and breathe around
a characteristic rhythmic feel. By defining that feel as a minimal skeleton, we
give downstream processes a clear, lightweight seed to elaborate from.

Example::

    >>> from accompy.rhythmic_skeletons import resolve_skeleton, apply_skeleton
    >>> resolve_skeleton("tresillo")
    (1.5, 1.5, 1)
    >>> resolve_skeleton((2, 2))
    (2, 2)

    >>> from accompy.converters import ChordSequence
    >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
    >>> expanded = apply_skeleton(cs, "tresillo")
    >>> [(sym, dur) for sym, dur in expanded]
    [('Dm7', 1.5), ('Dm7', 1.5), ('Dm7', 1.0), ('G7', 1.5), ('G7', 1.5), ('G7', 1.0)]
"""

from __future__ import annotations

from typing import Sequence, Union

# ---------------------------------------------------------------------------
# Built-in skeleton data
# ---------------------------------------------------------------------------

RHYTHMIC_SKELETONS: dict[str, dict] = {
    # === 4/4 patterns ===
    "whole_note": {
        "pattern": (4,),
        "name": "Whole note",
        "beats_per_measure": 4,
        "styles": ["ballad", "pad", "ambient", "slow_swing", "worship", "drone"],
    },
    "half_notes": {
        "pattern": (2, 2),
        "name": "Half notes",
        "beats_per_measure": 4,
        "styles": ["ballad", "hymn", "slow_rock", "ambient", "choral", "new_age"],
    },
    "quarter_notes": {
        "pattern": (1, 1, 1, 1),
        "name": "Quarter notes",
        "beats_per_measure": 4,
        "styles": ["rock", "pop", "march", "country", "motown"],
    },
    "four_on_the_floor": {
        "pattern": (1, 1, 1, 1),
        "name": "Four-on-the-floor",
        "beats_per_measure": 4,
        "styles": [
            "swing", "disco", "edm", "house", "country", "march",
            "polka", "techno", "pop", "motown",
        ],
    },
    "long_short_short": {
        "pattern": (2, 1, 1),
        "name": "Long-short-short",
        "beats_per_measure": 4,
        "styles": ["march", "polka", "country_rock", "folk", "bluegrass", "oom_pah"],
    },
    "short_short_long": {
        "pattern": (1, 1, 2),
        "name": "Short-short-long",
        "beats_per_measure": 4,
        "styles": ["folk", "power_ballad", "pop_rock", "singer_songwriter", "anthem"],
    },
    "short_long_short": {
        "pattern": (1, 2, 1),
        "name": "Short-long-short",
        "beats_per_measure": 4,
        "styles": ["pop", "soft_rock", "r_and_b", "soul", "gospel"],
    },
    "dotted_half_quarter": {
        "pattern": (3, 1),
        "name": "Dotted half + quarter",
        "beats_per_measure": 4,
        "styles": ["ballad", "hymn", "slow_swing", "waltz_feel", "classical"],
    },
    "quarter_dotted_half": {
        "pattern": (1, 3),
        "name": "Quarter + dotted half",
        "beats_per_measure": 4,
        "styles": ["ska", "reggae", "anticipation", "new_wave"],
    },
    "charleston": {
        "pattern": (1.5, 1.5, 1),
        "name": "Charleston",
        "beats_per_measure": 4,
        "styles": [
            "swing", "jazz", "funk", "bebop", "big_band",
            "jump_blues", "dixieland", "jive",
        ],
    },
    "reverse_charleston": {
        "pattern": (1, 1.5, 1.5),
        "name": "Reverse Charleston",
        "beats_per_measure": 4,
        "styles": ["bebop", "modern_jazz", "hard_bop", "post_bop", "cool_jazz"],
    },
    "displaced_charleston": {
        "pattern": (1.5, 1, 1.5),
        "name": "Displaced Charleston",
        "beats_per_measure": 4,
        "styles": ["latin_jazz", "afro_cuban", "fusion", "samba_jazz"],
    },
    "straight_eighths": {
        "pattern": (0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
        "name": "Straight eighths",
        "beats_per_measure": 4,
        "styles": [
            "rock", "pop", "bossa_nova", "punk", "new_wave",
            "indie", "surf", "rockabilly",
        ],
    },
    "long_and_push": {
        "pattern": (2, 1, 0.5, 0.5),
        "name": "Long + push",
        "beats_per_measure": 4,
        "styles": ["funk", "r_and_b", "neo_soul", "gospel", "hip_hop"],
    },
    "backbeat_pickup": {
        "pattern": (1, 1, 0.5, 0.5, 1),
        "name": "Backbeat with pickup",
        "beats_per_measure": 4,
        "styles": ["funk", "gospel", "soul", "motown", "blues_rock"],
    },
    "offbeat_skank": {
        "pattern": (0.5, 1.5, 0.5, 1.5),
        "name": "Off-beat skank",
        "beats_per_measure": 4,
        "styles": ["reggae", "ska", "dub", "dancehall", "rocksteady", "two_tone"],
    },
    "anticipated_two": {
        "pattern": (1, 0.5, 0.5, 1, 1),
        "name": "Anticipated 2",
        "beats_per_measure": 4,
        "styles": ["latin", "bossa_nova", "samba", "afro_cuban", "salsa"],
    },
    "push_four": {
        "pattern": (1, 1, 1, 0.5, 0.5),
        "name": "Push on 4",
        "beats_per_measure": 4,
        "styles": ["jazz", "swing", "blues", "jump_blues", "soul_jazz"],
    },
    "dotted_quarter_eighths": {
        "pattern": (1.5, 0.5, 1.5, 0.5),
        "name": "Dotted quarter + eighth",
        "beats_per_measure": 4,
        "styles": ["pop", "synth_pop", "disco", "euro_dance", "tropical"],
    },
    "tresillo": {
        "pattern": (1.5, 1.5, 1),
        "name": "Tresillo",
        "beats_per_measure": 4,
        "styles": [
            "afro_cuban", "reggaeton", "new_orleans", "hip_hop",
            "dancehall", "samba", "rumba", "trap",
        ],
    },
    "habanera": {
        "pattern": (1.5, 1, 1.5),
        "name": "Habanera",
        "beats_per_measure": 4,
        "styles": [
            "habanera", "tango", "afro_cuban", "latin_pop",
            "reggaeton", "beguine",
        ],
    },
    # === 3/4 patterns ===
    "waltz_whole": {
        "pattern": (3,),
        "name": "Dotted half",
        "beats_per_measure": 3,
        "styles": ["slow_waltz", "ballad", "ambient", "chorale"],
    },
    "waltz_quarters": {
        "pattern": (1, 1, 1),
        "name": "Waltz quarters",
        "beats_per_measure": 3,
        "styles": [
            "waltz", "oom_pah", "viennese_waltz", "country_waltz",
            "mazurka", "landler",
        ],
    },
    "waltz_half_quarter": {
        "pattern": (2, 1),
        "name": "Half + quarter",
        "beats_per_measure": 3,
        "styles": ["waltz", "minuet", "folk_waltz", "country_waltz"],
    },
    "waltz_quarter_half": {
        "pattern": (1, 2),
        "name": "Quarter + half",
        "beats_per_measure": 3,
        "styles": ["sarabande", "minuet", "slow_waltz", "classical"],
    },
    "waltz_dotted_quarters": {
        "pattern": (1.5, 1.5),
        "name": "Dotted quarters (6/8 feel)",
        "beats_per_measure": 3,
        "styles": ["jig", "tarantella", "irish", "6_8_rock", "blues_shuffle"],
    },
    "waltz_with_pickup": {
        "pattern": (1, 0.5, 0.5, 1),
        "name": "Waltz with pickup",
        "beats_per_measure": 3,
        "styles": ["viennese_waltz", "jazz_waltz", "show_tune"],
    },
    "waltz_eighth_lead": {
        "pattern": (0.5, 0.5, 1, 1),
        "name": "Eighth-note lead-in",
        "beats_per_measure": 3,
        "styles": ["folk_waltz", "jazz_waltz", "musette"],
    },
}


# ---------------------------------------------------------------------------
# Lookup indices
# ---------------------------------------------------------------------------

_BY_NAME: dict[str, str] = {}  # lowercased name → skeleton key
_BY_STYLE: dict[str, list[str]] = {}  # style → list of skeleton keys


def _rebuild_indices() -> None:
    """Rebuild the name and style lookup indices from RHYTHMIC_SKELETONS."""
    _BY_NAME.clear()
    _BY_STYLE.clear()
    for key, entry in RHYTHMIC_SKELETONS.items():
        name_lower = entry["name"].lower()
        # First key wins for a given name (avoids overwrite by aliases)
        if name_lower not in _BY_NAME:
            _BY_NAME[name_lower] = key
        for style in entry.get("styles", []):
            _BY_STYLE.setdefault(style, []).append(key)


_rebuild_indices()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_skeleton(
    skeleton: Union[str, tuple, Sequence],
) -> tuple:
    """Resolve a skeleton specification to a tuple of durations.

    Accepts:
        - A tuple or list of numbers (pass-through)
        - A skeleton key (e.g., ``"tresillo"``, ``"whole_note"``)
        - A skeleton name, case-insensitive (e.g., ``"Tresillo"``)
        - A style string (e.g., ``"reggae"``) — returns the first match

    Returns:
        Tuple of beat durations summing to the measure length.

    Raises:
        KeyError: If the skeleton cannot be resolved.

    Examples:
        >>> resolve_skeleton("whole_note")
        (4,)
        >>> resolve_skeleton("tresillo")
        (1.5, 1.5, 1)
        >>> resolve_skeleton((2, 2))
        (2, 2)
        >>> resolve_skeleton("Dotted half + quarter")
        (3, 1)
    """
    # Tuple / list pass-through
    if isinstance(skeleton, (tuple, list)):
        return tuple(skeleton)

    if not isinstance(skeleton, str):
        raise TypeError(
            f"skeleton must be a str, tuple, or list, got {type(skeleton).__name__}"
        )

    # 1. Exact key lookup
    if skeleton in RHYTHMIC_SKELETONS:
        return RHYTHMIC_SKELETONS[skeleton]["pattern"]

    # 2. Name lookup (case-insensitive)
    name_lower = skeleton.lower()
    if name_lower in _BY_NAME:
        return RHYTHMIC_SKELETONS[_BY_NAME[name_lower]]["pattern"]

    # 3. Style lookup
    if name_lower in _BY_STYLE:
        first_key = _BY_STYLE[name_lower][0]
        return RHYTHMIC_SKELETONS[first_key]["pattern"]

    # Not found — helpful error
    available_keys = list(RHYTHMIC_SKELETONS.keys())
    available_styles = sorted(_BY_STYLE.keys())
    raise KeyError(
        f"Unknown skeleton: {skeleton!r}. "
        f"Available keys: {available_keys[:10]}... "
        f"Available styles: {available_styles[:10]}..."
    )


def apply_skeleton(
    cs,  # ChordSequence — import deferred to avoid circular deps
    skeleton: Union[str, tuple, Sequence],
) -> "ChordSequence":
    """Apply a rhythmic skeleton to a chord sequence.

    The skeleton defines strike positions within each *measure*. Each strike
    plays whatever chord is active at that beat position. If a strike spans a
    chord boundary within a measure, it is split so the chord change is
    respected.

    Args:
        cs: A ChordSequence (from ``accompy.converters``).
        skeleton: Skeleton key, name, style, or duration tuple.

    Returns:
        A new ChordSequence with chords expanded according to the skeleton.

    Example:
        >>> from accompy.converters import ChordSequence
        >>> cs = ChordSequence([("Dm7", 2.0), ("G7", 2.0)])
        >>> result = apply_skeleton(cs, "tresillo")
        >>> [(s, d) for s, d in result]
        [('Dm7', 1.5), ('Dm7', 0.5), ('G7', 1.0), ('G7', 1.0)]
    """
    from .converters import ChordSequence

    pattern = resolve_skeleton(skeleton)
    beats_per_measure = sum(pattern)

    # Compute strike start times within a measure
    strike_starts = []
    t = 0.0
    for dur in pattern:
        strike_starts.append(t)
        t += dur
    # strike_starts[i] is the start, pattern[i] is the duration

    # Group input chords into measures
    measures = _group_into_measures(cs.chords, beats_per_measure)

    # Expand each measure
    expanded = []
    for measure_chords in measures:
        expanded.extend(
            _expand_measure(measure_chords, strike_starts, pattern, beats_per_measure)
        )

    return ChordSequence(
        chords=expanded,
        title=cs.title,
        key=cs.key,
        tempo=cs.tempo,
        time_signature=cs.time_signature,
    )


def register_skeleton(
    key: str,
    pattern: tuple,
    *,
    name: str = "",
    beats_per_measure: float | None = None,
    styles: list[str] | None = None,
) -> None:
    """Register a custom rhythmic skeleton.

    Args:
        key: Unique string key for the skeleton.
        pattern: Tuple of beat durations.
        name: Human-readable name (defaults to key).
        beats_per_measure: Measure length in beats (defaults to sum of pattern).
        styles: List of associated style strings.

    Example:
        >>> register_skeleton("my_groove", (1, 0.5, 0.5, 2), name="My Groove")
        >>> resolve_skeleton("my_groove")
        (1, 0.5, 0.5, 2)
    """
    if beats_per_measure is None:
        beats_per_measure = sum(pattern)
    RHYTHMIC_SKELETONS[key] = {
        "pattern": tuple(pattern),
        "name": name or key,
        "beats_per_measure": beats_per_measure,
        "styles": list(styles) if styles else [],
    }
    _rebuild_indices()


def list_skeletons(
    *,
    beats_per_measure: float | None = None,
    style: str | None = None,
) -> list[str]:
    """List available skeleton keys, optionally filtered.

    Args:
        beats_per_measure: Filter to skeletons matching this measure length.
        style: Filter to skeletons associated with this style.

    Returns:
        List of skeleton key strings.

    Examples:
        >>> "tresillo" in list_skeletons()
        True
        >>> all(RHYTHMIC_SKELETONS[k]["beats_per_measure"] == 3
        ...     for k in list_skeletons(beats_per_measure=3))
        True
    """
    keys = list(RHYTHMIC_SKELETONS.keys())
    if beats_per_measure is not None:
        keys = [
            k for k in keys
            if RHYTHMIC_SKELETONS[k]["beats_per_measure"] == beats_per_measure
        ]
    if style is not None:
        style_keys = set(_BY_STYLE.get(style, []))
        keys = [k for k in keys if k in style_keys]
    return keys


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EPSILON = 1e-9


def _group_into_measures(
    chords: list[tuple[str, float]], beats_per_measure: float
) -> list[list[tuple[str, float]]]:
    """Group chord events into measures of ``beats_per_measure`` beats.

    If a chord spans a measure boundary, it is split across measures.
    """
    measures: list[list[tuple[str, float]]] = []
    current_measure: list[tuple[str, float]] = []
    remaining_in_measure = beats_per_measure

    for symbol, duration in chords:
        dur_left = duration
        while dur_left > _EPSILON:
            take = min(dur_left, remaining_in_measure)
            current_measure.append((symbol, take))
            remaining_in_measure -= take
            dur_left -= take

            if remaining_in_measure < _EPSILON:
                measures.append(current_measure)
                current_measure = []
                remaining_in_measure = beats_per_measure

    # Flush any partial final measure
    if current_measure:
        measures.append(current_measure)

    return measures


def _expand_measure(
    measure_chords: list[tuple[str, float]],
    strike_starts: list[float],
    strike_durations: tuple,
    beats_per_measure: float,
) -> list[tuple[str, float]]:
    """Expand a single measure's chords according to skeleton strikes.

    Each skeleton strike plays whatever chord is active at that beat position.
    If a strike spans a chord boundary, it is split.
    """
    # Build chord map: list of (symbol, start, end) within the measure
    chord_map: list[tuple[str, float, float]] = []
    pos = 0.0
    for symbol, dur in measure_chords:
        chord_map.append((symbol, pos, pos + dur))
        pos += dur

    if not chord_map:
        return []

    result: list[tuple[str, float]] = []

    for i, strike_beat in enumerate(strike_starts):
        strike_dur = strike_durations[i]
        strike_end = strike_beat + strike_dur

        # Find all chords this strike overlaps
        for symbol, chord_start, chord_end in chord_map:
            # Overlap: [max(strike_beat, chord_start), min(strike_end, chord_end))
            overlap_start = max(strike_beat, chord_start)
            overlap_end = min(strike_end, chord_end)
            overlap_dur = overlap_end - overlap_start

            if overlap_dur > _EPSILON:
                result.append((symbol, overlap_dur))

    return result
