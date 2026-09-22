# accompy.realtime

Real-time accompaniment support (foundation).

This module provides the foundation for real-time accompaniment playback,
separating event scheduling from synthesis. This enables integration with
real-time audio systems like hum/pyo in the future.

#### NOTE
This is scaffolding for future work. Current implementation focuses on
event generation infrastructure. Real-time audio synthesis integration
with hum/pyo is planned for a future release.

### Classes

| [`RealtimeAccompaniment`](#accompy.realtime.RealtimeAccompaniment)([config, on_event])   | Real-time accompaniment player (foundation for future work).   |
|----------------------------------------------------------------------------------------------|----------------------------------------------------------------|

### *class* accompy.realtime.RealtimeAccompaniment(config=None, , on_event=None)

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
