import logging
import struct
from .trackevent import TrackEvent
from .midicodes import HEADER_INDICATOR, TRACK_INDICATOR
from . import util


logger = logging.getLogger("FileWriter")


class FileWriter:

    def __init__(self, filename: str, midi_type: int, time_division: int):
        if midi_type not in [0, 1, 2]:
            raise ValueError(f"Invalid midi type '{midi_type}'")
        if time_division < 1:
            raise ValueError(f"Time division must be greater than 0")
        self.filename = filename
        self.file_handle = None
        self.type = midi_type
        self.time_division = time_division
        self.current_track_offset = None
        self.track_count = 0
        self.extra_bytes = bytearray()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return

    def write_bytes(self, data, desc=""):
        logger.debug(f"Write {desc} at 0x{self.file_handle.tell():X}: {util.hex_dump(data)}")
        self.file_handle.write(data)

    def write_int(self, number: int, length: int, desc=""):
        data = number.to_bytes(length, 'big')
        self.write_bytes(data, desc)

    def open(self):
        self.file_handle = open(self.filename, "wb")
        self.write_bytes(HEADER_INDICATOR, "File header")
        header_length = struct.pack('>I', (6 + len(self.extra_bytes)))
        self.write_bytes(header_length, "hdr_len")
        self.write_int(self.type, 2, "type")
        self.write_int(1, 2, "track_count")
        self.write_int(self.time_division, 2, "division")
        if len(self.extra_bytes) > 0:
            self.write_bytes(self.extra_bytes)

    def close(self):
        if self.current_track_offset is not None:
            self.close_track()
        self.file_handle.seek(10)
        self.write_int(self.track_count, 2, "track_count_rewrite")
        self.file_handle.seek(0, 2)
        self.file_handle.close()
        self.file_handle = None

    def close_track(self):
        if self.current_track_offset is None:
            logger.warning("close_track called but no track open")
            return
        track_event_length = self.file_handle.tell() - self.current_track_offset - 8
        self.file_handle.seek(self.current_track_offset + 4)
        self.write_int(track_event_length, 4, "event_len_rewrite")
        self.current_track_offset = None
        self.file_handle.seek(0, 2)

    def new_track(self):
        if self.track_count > 1 and self.type == 0:
            raise RuntimeError("Type 0 files cannot have more than one track")
        if self.file_handle is None:
            raise RuntimeError("File not opened")
        if self.current_track_offset is not None:
            raise RuntimeError("Close existing track before creating a new one")
        self.file_handle.seek(0, 2)
        self.current_track_offset = self.file_handle.tell()
        self.track_count += 1
        logger.debug(f"Starting new track {self.track_count - 1} at offset 0x{self.current_track_offset:X}")
        self.write_bytes(TRACK_INDICATOR)
        self.write_int(0, 4, "event_len")

    def write_event(self, event: TrackEvent, delta_time=None):
        if delta_time is None:
            delta_time_bytes = event.time_bytes
        else:
            delta_time_bytes = util.int_to_var_len(delta_time)
        self.write_bytes(delta_time_bytes + event.event_bytes, "event")

    def add_time_signature(self, numerator: int, denominator: int, **kwargs):
        metronome = 18
        thirty_second = 8
        delta_time = 0
        for k, v in kwargs:
            if k == 'metronome':
                metronome = v
            elif k == 'thirty_second':
                thirty_second = v
            elif k == 'delta_time':
                delta_time = v
            else:
                raise ValueError(f"Unknown keyword argument '{k}'")
        ts_data = util.int_to_var_len(delta_time)
        dd = int(denominator ** (1/2))
        ts_data += b'\xFF\x58\x04'
        ts_data += numerator.to_bytes(1, 'big', signed=False)
        ts_data += dd.to_bytes(1, 'big', signed=False)
        ts_data += metronome.to_bytes(1, 'big', signed=False)
        ts_data += thirty_second.to_bytes(1, 'big', signed=False)
        self.write_bytes(ts_data, "time_sig")
        return

    def add_tempo(self, bpm: int, **kwargs):
        delta_time = 0
        for k, v in kwargs:
            if k == 'delta_time':
                delta_time = v
            else:
                raise ValueError(f"Unknown keyword argument '{k}'")
        event_bytes = util.int_to_var_len(delta_time)
        event_bytes += b'\xFF\x51\x03'
        usq = int(util.bpm_to_microseconds(bpm))
        event_bytes += usq.to_bytes(3, 'big', signed=False)
        self.write_bytes(event_bytes, "tempo")
