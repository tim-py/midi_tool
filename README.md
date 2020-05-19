# MIDI TOOLS
Various python modules and scripts for viewing and modifying MIDI files.
Designed for large files--MIDI events are read from the file one at a time
using generator functions.

### dump_midi_file.py
Useful for viewing MIDI events in elapsed time/measure.

### type_zero.py
Converts a type 1 MIDI file to type 0 with some tweaks:
* change meta data
* squash notes into a single channel

## TODO
* Type 2 support
* SMPTE timecode support
