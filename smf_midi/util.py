import logging
import smf_midi

root_logger = logging.getLogger()
LOG_FORMAT = '%(levelname)-8s %(message)s'
DEF_LOG_LEVEL = logging.INFO


def set_logging(logging_level=DEF_LOG_LEVEL, logging_format=LOG_FORMAT, **kwargs):

    for k, v in kwargs.items():
        if k == "debug":
            if v:
                logging_level = logging.DEBUG
        else:
            raise ValueError("Keyword {} invalid".format(k))

    # Check for existing stream (console) handlers and add if necessary
    for handler in root_logger.handlers:
        if type(handler) is logging.StreamHandler:
            con_handler = handler
            break
    else:
        con_handler = logging.StreamHandler()
        root_logger.addHandler(con_handler)

    # Set the appropriate logging format
    con_handler.setFormatter(logging.Formatter(logging_format))

    # Set the logging level for console handler
    con_handler.setLevel(logging_level)

    # Set the top level to highest handler level
    root_logger.setLevel(max([h.level for h in root_logger.handlers]))

    return


def debug_enabled():
    if root_logger.level <= 10:
        return True
    return False


def hex_dump(data, **kwargs):
    data_strings = []

    # Options
    printable = True
    for k, v in kwargs.items():
        if k == 'printable':
            if not v:
                printable = False
        else:
            raise ValueError("Keyword '{}' unrecognized".format(k))

    # Check if this is an iterable and return a single hex string if not
    try:
        _ = iter(data)
    except TypeError:
        return "0x{:02X}".format(data)

    # Loop through and check if this fails to be a string/unicode
    # or the string characters are outside the printable range, break out
    # otherwise we we will return the string
    string_parts = []
    for c in data:
        if type(c) is str:
            if (ord(c) < 32 or ord(c) > 126) or not printable:
                break
            string_parts.append(c)
        else:
            if (c < 32 or c > 126) or not printable:
                break
            string_parts.append(chr(c))
    else:
        return "'{}'".format(data)

    # Loop through data building a hex string
    for c in data:
        if type(c) is str:
            c = ord(c)
        data_strings.append("0x{:02X}".format(c))

    return " ".join(data_strings)


def calculate_note(note_value):

    if note_value < 0 or note_value > 127:
        return "*invalid*"

    note_names = ('C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B')

    mid_c = 60
    from_mid_c = note_value - mid_c
    octaves_below = int(from_mid_c / 12)
    octave = 4 + octaves_below
    name_index = from_mid_c % 12

    return "{}{}".format(note_names[name_index], octave)


def big_endian_to_unsigned(data):
    """
    Converts big endian bytes to int or long
    :param data: bytearray
    :return: int or long
    """

    value = 0
    shift = 0
    while len(data) > 0:
        value += (data.pop() << shift)
        shift += 8

    return value


def get_variable_length_quantity(data, **kwargs):
    """
    Get a varaible length value from data.  Bytes are big endian (MSB first) and bit 7 set indicates
    another byte must be read (data in bits 0 - 6), so we keep shifting the value over by 7 bits as we
    add the next 7 bits
    :param data: bytearray of strings
    :return: bytes of the variable length quantity
    """

    if type(data) is not bytearray:
        raise ValueError("Internal Error: expecting bytearray, found '{}'".format(type(data)))

    start = 0
    destructive = False
    for k, v in kwargs.items():
        if k == 'start':
            start = v
        elif k == 'destructive':
            if v:
                destructive = True
            else:
                destructive = False
        else:
            raise ValueError("Keyword {} invalid".format(k))

    value_bytes = bytearray()
    idx = start
    while len(data) > 0:
        value_bytes.append(data[idx])
        idx += 1
        # If bit 7 is cleared, this is the last 7 bits, break out and return
        if not (value_bytes[-1] & 128):
            break
    else:
        raise RuntimeError("Exhausted data (len={}) while extracting variable length field".format(len(data)))

    if destructive:
        for i in range(len(value_bytes)):
            data.pop(0)

    return value_bytes


def read_var_len_quantity(file_handle, offset=None):
    """
    Read in MIDI variable length quantity from a file. File is read one byte at a time until bit 7 is set.
    """
    if offset is not None:
        file_handle.seek(offset)

    quantity_bytes = bytearray()
    quantity_bytes.extend(file_handle.read(1))
    while quantity_bytes[-1] & 0x80:
        quantity_bytes.extend(file_handle.read(1))
    return quantity_bytes


def var_len_to_int(data):
    """
    Converts midi variable length data into an int
    :param data: bytearray
    :return: int or long (as necessary)
    """
    if type(data) is not bytearray:
        raise ValueError("Internal Error: expecting bytearray, found '{}'".format(type(data)))

    value = 0
    data_index = 0
    while len(data) > 0:
        b = data[data_index]
        data_index += 1
        overflow = b & 128
        base = b & 127
        value += base
        # If bit 7 is cleared, this is the last 7 bits, break out and return
        if overflow == 0:
            break
        # Bit 8 is set, so shift the accumulated value over by 7 bits to fit the next 7
        value <<= 7
    else:
        raise RuntimeError("Exhausted data while extracting variable length field")

    return value


def int_to_var_len(int_value: int):
    """
    Convert an integer into midi variable length data
    :param int_value: int
    :return: bytearray
    """

    if int_value < 0:
        # Cannot represent negative numbers using this method
        raise ValueError("Cannot convert negative integer to variable length value")

    # Create a byte array to hold the midi variable length number
    value_bytes = bytearray()

    # Put the least sig 7 bits into the array and shift the int right by 7
    value_bytes.insert(0, int_value & 127)
    int_value = int_value >> 7

    # Continue to insert each 7 bits (0-6) at the head of the list (big endian)
    # and set their bit 7 on to indicate another 7 bits follow
    while int_value > 0:

        # Pull least sig 7 bits (0 - 6) into lsb
        lsb = int_value & 127

        # Insert this byte at the beginning of the bytearray to make MSB first (big endian)
        value_bytes.insert(0, lsb | 128)

        # shift int_value to the right by 7 bits
        int_value = int_value >> 7

    return value_bytes


def pop_var_length_int(data):
    """
    Destructively pops bytes as a variable length integer from the beginning of data and converts it
    :param data: bytearray
    :return: VariableInteger object
    """

    class VariableInteger:

        def __init__(self, data_bytes=bytearray()):
            self.bytes = data_bytes

        @property
        def length(self):
            return len(self.bytes)

        @property
        def value(self):
            return var_len_to_int(self.bytes)

    return VariableInteger(get_variable_length_quantity(data, destructive=True))


def format_seconds_string(seconds):
    """
    Formats seconds as HH:MM:SS.S
    :param seconds:
    :return:
    """
    hour_string = ""
    minute_string = ""
    if seconds >= 3600:
        hours = seconds // 3600
        seconds -= (hours * 3600)
        hour_string = "{}h ".format(hours)
    if seconds > 60:
        minutes = seconds // 60
        seconds -= (minutes * 60)
        minute_string = "{}m ".format(minutes)
    return "{}{}{:.1f}s".format(hour_string, minute_string, seconds)


def merge_track_events(tracks):
    """
    Merges multiple tracks into one.  Keep in mind, things like track level program changes inside the track
    may not make sense to merge together.  Care should be taken.
    :param tracks: list of list of TrackEvent objects
    :return: list of TrackEvent objects
    """

    merged_track = []
    track_count = len(tracks)

    #
    # First grab any non-note events at delta 0 and add merge them. This puts all the meta, controller, etc
    # events for all tracks at the beginning just to make things look better on output.
    track_id = 0
    for track in tracks:
        # Append events from this track until we reach a note event or no more events
        pulled = 0
        while True:
            if len(track) < 1:
                break
            event = track[0]
            if event.is_end_of_track:
                break
            if event.get_delta_ticks() != 0:
                break
            if event.type_desc in smf_midi.TrackEvent.NOTE_EVENTS:
                break
            merged_track.append(track.pop(0))
            pulled += 1
        root_logger.debug("Pulled {} non-note events from track {} - next delta is {}".format(
            pulled, track_id, track[0].get_delta_ticks()
        ))
        track_id += 1

    #
    # Initialize the track times for each track. We use None if the
    # track has no events (possible due to other type of processing)
    track_times = []
    for idx in range(track_count):
        track = tracks[idx]
        if len(track) > 0:
            # First event of this track
            event = track[0]
            # Check for end of track event
            if event.is_end_of_track:
                if len(track) > 1:
                    root_logger.warning(f"Track {idx} has EOT as first event, but {len(track) - 1}"
                                        " events follow--ignoring the rest")
                else:
                    root_logger.debug("Track {} has EOT as first event--flushing track data".format(idx))
                tracks[idx] = []
                track_times.append(None)
                continue

            track_times.append(event.get_delta_ticks())
        else:
            track_times.append(None)
    root_logger.debug("Initialized track times: {}".format(track_times))

    #
    # Loop until break (all source tracks are empty)
    last_event_time = 0
    while True:

        # Determine the smallest time delta value across all tracks
        min_track_time = None
        for track_time in track_times:
            if track_time is None:
                continue
            if min_track_time is None:
                min_track_time = track_time
            elif track_time < min_track_time:
                min_track_time = track_time

        # If min_delta is None, there are no more events in any track
        if min_track_time is None:
            break

        # Set the current time to the lowest track time
        current_time = min_track_time

        # Loop through each track pulling events at the current time
        for idx in range(track_count):

            track = tracks[idx]
            if len(track) < 1 or track_times[idx] is None:
                continue

            while track_times[idx] == current_time:

                # Get the first event for this track
                event = track.pop(0)

                # Set the event's time delta for the new merged track
                event.set_delta_ticks(current_time - last_event_time)

                # Check for end of track event
                if event.is_end_of_track:
                    if len(track) > 1:
                        root_logger.warning("Track {} has EOT but {} events follow--ignoring the rest".format(
                            idx, len(track) - 1
                        ))
                    else:
                        root_logger.debug("Track {} has reached EOT event".format(idx))
                    tracks[idx] = []
                    track_times[idx] = None
                    continue

                # Now add this event to the new merged track
                merged_track.append(event)

                # Save the current time as the last event time
                last_event_time = current_time

                # Set the track time to the time of the next event in the track
                if len(track) > 0:
                    track_times[idx] += track[0].get_delta_ticks()
                else:
                    track_times[idx] = None

    # Create a new end of track event at delta 0 and add it to the end of the track
    eot_event = smf_midi.TrackEvent(bytearray(b'\x00') + smf_midi.TrackEvent.END_OF_TRACK_MARKER)
    merged_track.append(eot_event)

    return merged_track


def filter_events(events):
    """
    Filters out non-note events.  Tempo, time signatures, and of course end-of-track are also kept.
    This is useful to remove all controller and program changes to convert a song for a specific
    midi instrument
    :param events: list of events
    :return: int - number of events dropped
    """

    if type(events) is not list:
        raise ValueError("events must be a list of TrackEvent objects")

    drop_count = 0
    eot_event = False
    idx = 0
    current_ticks = 0
    previous_ticks = 0
    while True:

        if len(events) < 1:
            break
        if idx >= len(events):
            break

        if eot_event:
            raise ValueError("Reached end-of-track event not last event in track")

        # Save the event's delta
        delta = events[idx].get_delta_ticks()
        current_ticks += delta

        # Get the event for cleaner code
        event = events[idx]

        # Events to keep, increment the idx to skip over it
        if event.type_desc in smf_midi.TrackEvent.NOTE_EVENTS or event.is_time_signature \
                or event.is_tempo or event.is_end_of_track:
            event.set_delta_ticks(current_ticks - previous_ticks)
            previous_ticks = current_ticks
            if event.is_end_of_track:
                eot_event = True
            idx += 1
            continue

        # Drop the event from the list
        root_logger.debug("Dropping event delta={} {}".format(delta, event.description))
        events.pop(idx)
        drop_count += 1

    return drop_count


def change_channels(events, new_channel=None, **kwargs):
    """
    Change midi channel number on all channel events.  Either set all channels to one (using new_channel)
    or provide a dictionary (assign= keyword) for each channel to be assigned.
    :param events: list of TrackEvent objects
    :param new_channel: int - assign ALL channels to this channel
    :param kwargs:
                    assign=dict - key is current channel (int) value is new channel (int)
    :return: int - number of events that were re-assigned
    """

    root_logger.debug("Changing channels: new_channel={} kwargs: {}".format(new_channel, kwargs))

    assignments = {}

    for k, v in kwargs.items():
        if k == 'assign':
            if new_channel is not None:
                raise RuntimeError("new_channel and assign keyword are mutually exclusive")
            if type(v) is not dict:
                raise ValueError("assign keyword must have dictionary value")
            assignments = v

    if new_channel is not None:
        if type(new_channel) is not int:
            raise TypeError("new channel must be int")
        for i in range(16):
            assignments[i] = new_channel

    if len(assignments.keys()) < 1:
        raise RuntimeError("No channel assignments provided")

    re_assign_count = 0
    for event in events:
        if not event.is_channel_event:
            continue
        channel = event.get_channel()
        if channel in assignments.keys():
            event.set_channel(int(assignments[channel]))
            re_assign_count += 1

    return re_assign_count


def microseconds_to_bpm(usq: int):
    return int(60000000 / usq)


def bpm_to_microseconds(bpm: int):
    return int(60000000 / bpm)