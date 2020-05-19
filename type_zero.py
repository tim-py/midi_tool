import argparse
import smf_midi
import logging


opt = None
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("run_convert")


def get_options():
    """
    Parses the command line options
    """
    global opt

    # Create a parser object
    parser = argparse.ArgumentParser(description='Convert Type 1 MIDI to Type 0 with custom settings')

    # Positional required arguments
    parser.add_argument('file_in',
                        help="Name of the input MIDI file")
    parser.add_argument('file_out',
                        help="Name of the output MIDI file")

    # Optional keyword arguments
    parser.add_argument('--name', required=False,
                        help="Name of track--replace existing names")
    parser.add_argument('--text', required=False, action='append',
                        help="Text for track--replace existing text")
    parser.add_argument('--squash', required=False, type=int,
                        help="Channel number to squash all notes into")
    parser.add_argument('--debug', action="store_true", dest='debug', required=False,
                        help="Additional features for debugging")
    opt = parser.parse_args()


def main():

    exclusions = []

    get_options()
    if opt.squash and opt.squash not in range(1,16):
        raise ValueError("Squash value must be a channel number 1-15")

    midi_reader = smf_midi.FileReader(opt.file_in)
    if midi_reader.type == 0:
        raise RuntimeError(f"Midi file '{opt.file_in}' is already a type 0 file")
    if midi_reader.type != 1:
        raise RuntimeError(f"Midi file type {midi_reader.type} not supported")

    with smf_midi.FileWriter(opt.file_out, 0, midi_reader.time) as midi_writer:

        midi_writer.new_track()
        if opt.name:
            name_meta = smf_midi.TrackEvent.new_track_name(opt.name)
            midi_writer.write_event(name_meta)
            exclusions.append(name_meta.event_bytes[:2])
        if opt.text:
            for option_text in opt.text:
                text_meta = smf_midi.TrackEvent.new_text(option_text)
                midi_writer.write_event(text_meta)
            exclusions.append(text_meta.event_bytes[:2])
        for event in midi_reader.get_events_from_tracks(omit_events=exclusions, squash=opt.squash):
            midi_writer.write_event(event)


if __name__ == '__main__':
    main()
