from . import util
from . import midicodes


class TimeSignature:

    def __init__(self, data: bytearray):
        if len(data) < 4:
            raise ValueError("Invalid TimeSignature data '{}'".format(util.hex_dump(data)))
        self.nn, self.dd, self.clocks_per_metronome_click, self.thirty_seconds_per_quarter = data[-4:]
        return

    @staticmethod
    def string(data):
        if len(data) < 4:
            raise ValueError("Invalid TimeSignature data '{}'".format(util.hex_dump(data)))
        nn, dd, _, _ = data[-4:]
        return f"{nn}/{2 ** dd}"

    @property
    def data(self):
        return bytearray((self.nn, self.dd, self.clocks_per_metronome_click, self.thirty_seconds_per_quarter))

    @property
    def numerator(self):
        return self.nn

    @property
    def denominator(self):
        return 2 ** self.dd

    @property
    def meta_event(self):
        # Returns all meta event bytes following (but not including) time delta
        return b'\xff\x58\x04' + self.data[-4:]


class TrackEvent:

    # event types
    UNKNOWN = "UNKNOWN EVENT"
    TRACK_PROGRAM = "TRACK PROGRAM CHANGE"
    SYSEX = "SYSTEM EXCLUSIVE"
    META = "META EVENT"
    CHANNEL_NOTE = "CHANNEL NOTE EVENT"
    CHANNEL_CONTROLLER = "CHANNEL CONTROLLER CHANGE"
    CHANNEL_PROGRAM = "CHANNEL PROGRAM CHANGE"
    CHANNEL_PRESSURE = "CHANNEL KEY PRESSURE"
    CHANNEL_PITCH = "CHANNEL PITCH BEND"
    CHANNEL_POLY_PRESSURE = "POLYPHONIC KEY PRESSURE"

    def __init__(self, midi_file=None):
        self.event_offset = 0
        self.time_bytes = bytearray()
        self.event_bytes = bytearray()
        self.subtype = ""
        self.event_data = bytearray()

        if midi_file is not None:
            self.read_file(midi_file)

        return

    def read_file(self, midi_file):
        """
        Reads in a midi event (starting with time delta) from a file.  midi_file is an open file object
        and the current pointer must be at the beginning of the event.
        """

        # When called save the position as the beginning of this event
        self.event_offset = midi_file.tell()

        # Read the time bytes, saving current state values of timer
        self.time_bytes = util.read_var_len_quantity(midi_file)

        # Read the first byte of the event data which contains the type
        type_byte = midi_file.read(1)
        self.event_bytes.extend(type_byte)

        # Now that the first byte has been loaded into event_bytes, we can use the type property
        if self.type == self.TRACK_PROGRAM:
            # no further bytes are needed
            pass
        elif self.type == self.SYSEX or self.type == self.META:
            # get the SYSEX/META id/subtype
            subtype = midi_file.read(1)
            self.event_bytes.extend(subtype)
            subint = int.from_bytes(subtype, byteorder='big', signed=False)
            if self.type == self.SYSEX:
                self.subtype = f"ID=0x{subint:X}"
            else:
                self.subtype = midicodes.META_EVENT_TYPES[subint]
            # get the length of the data
            length_bytes = util.read_var_len_quantity(midi_file)
            self.event_bytes.extend(length_bytes)
            data_length = util.var_len_to_int(length_bytes)
            # Get the event data
            self.event_data = midi_file.read(data_length)
            self.event_bytes.extend(self.event_data)
        elif self.type in (self.CHANNEL_NOTE,
                           self.CHANNEL_POLY_PRESSURE,
                           self.CHANNEL_CONTROLLER,
                           self.CHANNEL_PITCH):
            # event has 2 more bytes of data
            self.event_data = midi_file.read(2)
            self.event_bytes.extend(self.event_data)
        elif self.type in (self.CHANNEL_PROGRAM, self.CHANNEL_PRESSURE):
            # event has one more byte of data
            # event has 2 more bytes of data
            self.event_data = midi_file.read(1)
            self.event_bytes.extend(self.event_data)
        else:
            raise RuntimeError("Unknown MIDI event 0x{:X} ({})".format(type_byte, type_byte))

        return

    def set_delta_ticks(self, delta: int):
        self.time_bytes = util.int_to_var_len(delta)

    @property
    def time_signature(self):
        if self.type == self.META and self.event_bytes[1] == 0x58:
            return TimeSignature(self.event_data)
        return None

    @property
    def tempo(self):
        """
        Tempo in microsonds per quarternote
        """
        if self.type == self.META and self.event_bytes[1] == 0x51:
            return int.from_bytes(self.event_data, byteorder="big", signed=False)
        return False

    @property
    def delta_ticks(self):
        return util.var_len_to_int(self.time_bytes)

    @property
    def type(self):
        event_type = self.event_bytes[0]
        event_nibble = event_type & 0xF0
        if event_type < 0x80:
            return self.TRACK_PROGRAM
        elif event_type == 0xF0 or event_type == 0xF7:
            return self.SYSEX
        elif event_type == 0xFF:
            return self.META
        elif event_nibble == 0x80 or event_nibble == 0x90:
            return self.CHANNEL_NOTE
        elif event_nibble == 0xA0:
            return self.CHANNEL_POLY_PRESSURE
        elif event_nibble == 0xB0:
            return self.CHANNEL_CONTROLLER
        elif event_nibble == 0xC0:
            return self.CHANNEL_PROGRAM
        elif event_nibble == 0xD0:
            return self.CHANNEL_PRESSURE
        elif event_nibble == 0xE0:
            return self.CHANNEL_PITCH
        return self.UNKNOWN

    @property
    def metadata(self):
        if self.type != self.META:
            return ""
        data = self.event_bytes[2:]
        util.pop_var_length_int(data)
        return data.decode('utf-8')

    @property
    def description(self):

        event_id = self.event_bytes[0]
        if self.type == self.TRACK_PROGRAM:
            return "0x{:X} ({}) Track Program '{}'".format(event_id, event_id, midicodes.PROGRAMS[event_id])
        elif self.type == self.META:
            meta_id = self.event_bytes[1]
            if meta_id in midicodes.META_EVENT_TYPES:
                meta_name = midicodes.META_EVENT_TYPES[meta_id]
            else:
                meta_name = "*UNKOWN META EVENT*"
            info = ""
            # Add info for time signature
            if meta_id == 0x58:
                info = f" {TimeSignature.string(self.event_bytes)}"
            elif meta_id == 0x51:
                info = f" {self.tempo}us/q  ({util.microseconds_to_bpm(self.tempo)}bpm)"
            else:
                metadata = self.metadata
                if len(metadata) > 0:
                    info = f" '{self.metadata}'"
            return f"0x{event_id:X} Meta 0x{meta_id:X} ({meta_id}) {meta_name}{info}"
        elif self.type == self.SYSEX:
            if len(self.event_bytes) > 2:
                sysex_data = util.hex_dump(self.event_bytes[2:])
            else:
                sysex_data = "*no data*"
            return "0x{:X} Sysex '{}'".format(event_id, sysex_data)
        elif self.type == self.CHANNEL_NOTE:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            note_name = util.calculate_note(self.event_bytes[1])
            if channel_event == 0x90:
                on_off = "on"
            else:
                on_off = "off"
            velocity = "0x{:X} ({})".format(self.event_bytes[2], self.event_bytes[2])
            return "0x{:X} Channel={} note {} {} velocity={}".format(
                channel_event, channel_id, note_name, on_off, velocity)
        elif self.type == self.CHANNEL_POLY_PRESSURE:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            note_name = util.calculate_note(self.event_bytes[1])
            velocity = "0x{:X} ({})".format(self.event_bytes[2], self.event_bytes[2])
            return "0x{:X} Channel={} aftertouch {} velocity={}".format(
                channel_event, channel_id, note_name, velocity)
        elif self.type == self.CHANNEL_CONTROLLER:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            controller_id = self.event_bytes[1]
            if controller_id in midicodes.CONTROLLER_MESSAGE:
                controller_name = midicodes.CONTROLLER_MESSAGE[controller_id]
            else:
                controller_name = "*UNKNOWN*"
            controller = "0x{:2X} ({}) {}".format(controller_id, controller_id, controller_name)
            value = "0x{:X} ({})".format(self.event_bytes[2], self.event_bytes[2])
            return "0x{:X} Channel={} Controller {}  value={}".format(
                channel_event, channel_id, controller, value)
        elif self.type == self.CHANNEL_PROGRAM:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            if self.event_bytes[1] < len(midicodes.PROGRAMS):
                channel_program = midicodes.PROGRAMS[self.event_bytes[1]]
            else:
                channel_program = "*unknown*"
            return "0x{:X} Channel={} program={} '{}'".format(
                channel_event, channel_id, self.event_bytes[1] + 1, channel_program)
        elif self.type == self.CHANNEL_PRESSURE:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            return "0x{:X} Channel={} pressure={}".format(
                channel_event, channel_id, self.event_bytes[1])
        elif self.type == self.CHANNEL_PITCH:
            channel_id = event_id & 0x0F
            channel_event = event_id & 0xF0
            return "0x{:X} Channel={} pitch bend={}".format(
                channel_event, channel_id, self.event_bytes[1])

        return "*UNKNOWN EVENT*"

    @property
    def is_channel_event(self):
        if self.type in (self.CHANNEL_NOTE,
                         self.CHANNEL_CONTROLLER,
                         self.CHANNEL_PROGRAM,
                         self.CHANNEL_PRESSURE,
                         self.CHANNEL_PITCH,
                         self.CHANNEL_POLY_PRESSURE):
            return True
        return False

    @property
    def channel(self):
        if not self.is_channel_event:
            return 0
        return self.event_bytes[0] & 0x0F

    def set_channel(self, channel: int):
        if not self.is_channel_event:
            raise TypeError("Event type is not channel event")
        if channel not in range(1,16):
            raise ValueError("Channel ID must be between 1 and 15")
        channel_command = self.event_bytes[0]
        channel_command = (channel_command & 0xF0) | channel
        self.event_bytes[0] = channel_command

    def copy(self, delta_ticks=0):
        new_event = TrackEvent()
        new_event.event_bytes = self.event_bytes
        new_event.time_bytes = util.int_to_var_len(delta_ticks)
        return new_event

    def __str__(self):
        return self.description

    def __repr__(self):
        return self.time_bytes + self.event_bytes

    @classmethod
    def new_track_name(cls, name, delta_time=0):
        event = cls()
        event.time_bytes = util.int_to_var_len(delta_time)
        event.event_bytes = b'\xFF\x03' + util.int_to_var_len(len(name)) + name.encode('utf-8')
        return event

    @classmethod
    def new_text(cls, name, delta_time=0):
        event = cls()
        event.time_bytes = util.int_to_var_len(delta_time)
        event.event_bytes = b'\xFF\x01' + util.int_to_var_len(len(name)) + name.encode('utf-8')
        return event
