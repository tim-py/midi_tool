import argparse
from smf_midi import FileReader, util, TrackEvent, Timer
import logging

opt = None

time_signatures = {}
tempo_changes = {}
time_division = 0


def get_options():
    """
    Parses the command line options
    """
    global opt

    # Create a parser object
    parser = argparse.ArgumentParser(description='Dump MIDI data to stdout')

    # Positional required arguments
    parser.add_argument('filename',
                        help="Name of the MIDI file to dump")

    # Optional keyword arguments
    parser.add_argument('--select', action='append', dest='select', required=False,
                        help="Selection <chan>:<start>:<end>")
    parser.add_argument('--skip-notes', action="store_true", dest='skip_notes', required=False,
                        help="Print only non-note data")
    parser.add_argument('--debug', action="store_true", dest='debug', required=False,
                        help="Additional features for debugging")
    opt = parser.parse_args()


def print_header_dump(midi_file: FileReader):
    print(f"|{'HEADER':=^31}|")
    print("| type | tracks | time division |")
    print(f"| {midi_file.type:^4} | {midi_file.track_count:^6} | {midi_file.time:^13} |")


def print_track_dump(midi_file: FileReader):
    track_number = 0
    for track in midi_file.tracks:
        track_string = f"TRACK {track_number}"
        print(f"\n|{track_string:=^144}|")
        print(f"| {'offset':^14} | {'time':^47} | {'event':^75} |")
        print(f"| {'hex':^6} {'(dec)':^7} | {'delta':6} | {'ticks':^8} | {'et':^12} "
              f"| {'measure':^12} | {'description':^75} |")
        print("-" * 146)
        ticks = 0
        time_signature = None
        tempo = 0
        timer = Timer(time_division, time_signatures, tempo_changes)
        for event in track.get_events():
            timer.update_event(event)
            print_event_detail(event, timer.current_time, timer.absolute_ticks, timer.current_measure)
        track_number += 1

    return


def print_event_detail(event: TrackEvent, et: str, at_ticks: int, measure_bar: str):
    if len(event.description) > 75:
        desc = event.description[:72] + "..."
    else:
        desc = event.description
    offset_string = f"0x{event.event_offset:04X} ({event.event_offset:05n})"
    print(f"| {offset_string} | {event.delta_ticks:6} | {at_ticks:8} | {et:>12} "
          f"| {measure_bar:>12} | {desc:75} |")
    return


def main():

    global time_division

    get_options()

    util.set_logging(debug=opt.debug)
    midi_file = FileReader()
    midi_file.read_file(opt.filename)
    time_division = midi_file.time
    print_header_dump(midi_file)
    print_track_dump(midi_file)

    return


if __name__ == '__main__':
    main()
