import logging
import struct
from . import util
from .track import Track
from .trackevent import TrackEvent
from .midicodes import HEADER_INDICATOR, END_OF_TRACK_INDICATOR

logger = logging.getLogger("FileReader")


class FileReader:

    def __init__(self, file_name=None):

        self.length = -1
        self.type = -1
        self.track_count = -1
        self.time = -1
        self.extra_bytes = bytearray()
        self.start_of_tracks = 0
        self.file_name = ""
        self.tracks = []

        if file_name is not None:
            self.read_file(file_name)

    def read_file(self, file_name: str):

        self.file_name = file_name
        offset = 0
        with open(self.file_name, "rb") as file_handle:

            logger.debug("Reading file header...")

            # Read the MThd midi header identifier (4 bytes)
            midi_indicator = file_handle.read(4)
            logger.debug("   Offset=0x{:X} Header Indicator {} hex={}".format(
                offset, midi_indicator, util.hex_dump(midi_indicator, printable=False)))
            if midi_indicator != HEADER_INDICATOR:
                raise RuntimeError(f"File should start with {HEADER_INDICATOR} found '{midi_indicator}'")

            # Read the length of the remaining file header (4 bytes)
            offset = file_handle.tell()
            chunk = file_handle.read(4)
            self.length = struct.unpack('>I', chunk)[0]
            logger.debug("   Offset=0x{:X} Header Length {} hex={}".format(
                offset, self.length, util.hex_dump(chunk, printable=False)))

            # Read the rest of the file header (using length, but is usually 6 bytes)
            offset = file_handle.tell()
            chunk = file_handle.read(self.length)
            logger.debug("   Offset=0x{:X} Header Data hex={}".format(offset, util.hex_dump(chunk, printable=False)))

            # Unpack the file type
            if len(chunk) > 1:
                self.type = struct.unpack('>H', chunk[0:2])[0]
                logger.debug("      file type={} hex={}".format(self.type, util.hex_dump(chunk[0:2])))
            else:
                logger.warning("Unable to read file type from header")

            # Unpack the track count
            if len(chunk) > 3:
                self.track_count = struct.unpack('>H', chunk[2:4])[0]
                logger.debug("      track count={} hex={}".format(self.track_count, util.hex_dump(chunk[2:4])))
            else:
                logger.warning("Unable to read number of tracks from header")

            # Unpack the time division
            if len(chunk) > 5:
                # Convert the bytes to int and save in time property
                self.time = struct.unpack('>H', chunk[4:6])[0]
                # Update the timer object with the value
                logger.debug("      time division={} hex={}".format(self.time, util.hex_dump(chunk[4:6])))
            else:
                logger.warning("Unable to read time division from header")

            # check for extra bytes
            if len(chunk) > 6:
                self.extra_bytes = bytearray(chunk[6:])
                logger.debug("Found {} extra header bytes".format(len(self.extra_bytes)))

            self.start_of_tracks = file_handle.tell()

        self._load_tracks()

        return

    def _load_tracks(self):
        current_offset = self.start_of_tracks
        for track_idx in range(self.track_count):
            logger.debug(f"Reading track {track_idx}")
            midi_track = Track()
            midi_track.read_track(self.file_name, current_offset)
            current_offset = midi_track.end_of_track_offset
            self.tracks.append(midi_track)

    def get_events_from_tracks(self, **kwargs):
        """
        Generator to read events from multiple tracks, yielding them as though they were in a single track;
        correcting time delta and eliminating duplicate events.
        """
        squash_channel = 0
        include = list(range(len(self.tracks)))
        omit_events = [END_OF_TRACK_INDICATOR]
        for k, v in kwargs.items():
            if k == 'include':
                if type(v) is not list:
                    raise ValueError("Include must be list")
                include = v
            elif k == 'omit_events':
                omit_events.extend(v)
            elif k == 'squash':
                squash_channel = int(v)
            else:
                raise ValueError(f"Keyword '{k}' invalid")

        current_time = 0
        current_delta = 0
        time_signatures = {}
        tempos = {}

        # Initialize all track event generators
        track_db = {}
        track_no = 0
        for track in self.tracks:
            if track_no not in include:
                logger.info(f"Skipping track '{track_no}'--not in included tracks")
            track.set_timer(self.time, time_signatures, tempos)
            track_info = {'generator': track.get_events(omit=omit_events, squash=squash_channel)}
            try:
                track_info['next_event'] = next(track_info['generator'])
            except StopIteration:
                continue
            track_db[track] = track_info
            track_no += 1

        while len(track_db) > 0:

            # Get the list of generators
            track_list = list(track_db.keys())

            # Loop through each of the generators, looking for all events
            # at the current time and finding the next time
            next_times = []
            current_events = []
            for track in track_list:

                track_info = track_db[track]
                event = track_info['next_event']

                # While this event is at the current time yield it first, then get the next one
                failsafe = 100000
                while track.timer.absolute_ticks == current_time:

                    failsafe -= 1
                    if failsafe < 0:
                        raise RuntimeError("FAILSAFE: Infinite loop detected")

                    if event.event_bytes not in current_events:
                        event.set_delta_ticks(current_delta)
                        yield event
                        current_events.append(event.event_bytes)

                    # Once we yield an event at this delta, we must zero it out again for future
                    # events at the current_time
                    current_delta = 0
                    try:
                        # Get the next event and put it in the dict value
                        event = next(track_info['generator'])
                        track_info['next_event'] = event
                    except StopIteration:
                        # If this generator is out of events, remove it from the dict
                        # to the next generator
                        track_db.pop(track)
                        break

                # At this point so long as this generator is still in the list, the event in the
                # dict value should be in the future, append the ticks to the list
                if track in track_db:
                    next_times.append(track.timer.absolute_ticks)

            # At this point all events for the current time have been yielded.  Let's find the next
            # absolute time using the min on all the times and loop again
            if len(next_times) > 0:
                next_time = min(next_times)
                current_delta = next_time - current_time
                current_time = next_time

        # Create an end-of-track event
        eot = TrackEvent()
        eot.set_delta_ticks(0)
        eot.event_bytes = END_OF_TRACK_INDICATOR
        yield eot

        return

    @property
    def bytes(self):
        byte_values = HEADER_INDICATOR
        byte_values.extend(struct.pack('>I', (6 + len(self.extra_bytes))))
        byte_values.extend(struct.pack('>H', self.type))
        byte_values.extend(struct.pack('>H', self.track_count))
        byte_values.extend(struct.pack('>H', self.time))
        byte_values.extend(self.extra_bytes)
        return byte_values

    @property
    def is_metrical_timing(self):
        if self.time & 0x8000:
            return False
        return True

    @property
    def is_time_code_timing(self):
        if self.time & 0x8000:
            return True
        return False
