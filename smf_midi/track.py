import logging
import struct
from .trackevent import TrackEvent
from .midicodes import TRACK_INDICATOR
from .timer import Timer


logger = logging.getLogger("Track")


class Track:

    def __init__(self):
        self.filename = ""
        self._start_offset = 0
        self.start_events = self._start_offset
        self.header_bytes = bytearray()
        self.track_event_length = 0
        self.timer = None

    @property
    def end_of_track_offset(self):
        return self.start_events + self.track_event_length

    def read_track(self, filename: str, start_offset: int):

        self.filename = filename
        self._start_offset = start_offset
        with open(self.filename, "rb") as fh:
            # Initialize
            fh.seek(self._start_offset)

            # Read in the track indicator
            midi_indicator = fh.read(4)

            if midi_indicator != TRACK_INDICATOR:
                raise RuntimeError(f"Track must start with '{TRACK_INDICATOR}' found '{midi_indicator}'")

            # Read in the track length
            chunk = fh.read(4)
            self.track_event_length = struct.unpack('>I', chunk)[0]
            logger.debug(f"Track: offset=0x{self._start_offset:X} ({self._start_offset})  "
                         f"total_length (incl hdr)={8 + self.track_event_length} bytes")

            # Save the current file offset as beginning of track events
            self.start_events = fh.tell()

        return

    def get_events(self, **kwargs):
        """
        Generator to iterate through each track event. Each event is read from the source file and yielded, so
        any changes will not persist if generator is started from the beginning again.
        """
        squash_channel = 0
        omit = []
        include = []
        for k, v in kwargs.items():
            if k == 'omit':
                omit = v
            elif k == 'include':
                include = v
            elif k == 'squash':
                squash_channel = int(v)
            else:
                raise ValueError(f"Keyword '{k}' invalid")

        with open(self.filename, "rb") as fh:

            # Move the file pointer to the start of the events
            fh.seek(self.start_events)

            # Loop through each event
            while fh.tell() < self.end_of_track_offset:

                # Create a TrackEvent from the data
                event = TrackEvent(fh)
                yield_event = True

                # If we have a timer provided, update it
                if self.timer is not None:
                    self.timer.update_event(event)

                # Handle channel squashing
                if squash_channel > 0 and event.is_channel_event:
                    if event.channel & 0xF != squash_channel:
                        if event.type == event.CHANNEL_NOTE:
                            event.set_channel(squash_channel)
                        else:
                            # Skip any non-note events as this could produce undesirable results
                            yield_event = False

                if yield_event:
                    for omit_bytes in omit:
                        if event.event_bytes.startswith(omit_bytes):
                            logger.debug(f"Skipping (omit) event {event.event_bytes}")
                            yield_event = False
                            break

                if include and yield_event:
                    for include_bytes in include:
                        if not event.event_bytes.startswith(include_bytes):
                            logger.debug(f"Skipping (include) event {event.event_bytes}")
                            yield_event = False
                            break

                if yield_event:
                    yield event

        return

    def set_timer(self, division: int, timesignatures: dict, tempos: dict):
        self.timer = Timer(division, timesignatures, tempos)
