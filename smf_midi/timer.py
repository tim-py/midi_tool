from .trackevent import TrackEvent


class Timer:
    """
    Class used for keeping track of measure and time position within a midi track.  It must be instantiated one per
    track.  The division is the integer value derived from the file header.  The time_signatures must be a dictionary
    of TimeSignature objects indexed by the absolute midi tick location and the tempos dictionary is the same but
    containing integer values from the tempo events.  These dictionaries can be pre-loaded by reading track 0 from
    a type 1 or 2 midi file or updated in process for type 0 or reading all tracks in parallel.  Each event MUST
    use the update_ticks OR update_event method to keep the timing correct.
    """

    def __init__(self, division: int, time_signatures: dict, tempos: dict):
        self.absolute_ticks = 0
        self.absolute_seconds = 0
        self.measure_ticks = 0
        self.measure_beats = 0
        self.measures = 0
        self.division = division
        self.time_signatures = time_signatures
        self.tempos = tempos

    @property
    def current_measure(self):
        # Represent as integers and covert from zero based to one based for measure and beat
        return f"{int(self.measures)+1}:{int(self.measure_beats) + 1}.{int(self.measure_ticks):03}"

    @property
    def current_time(self):
        minutes = int(self.absolute_seconds // 60)
        seconds = self.absolute_seconds % 60
        hours = int(minutes // 60)
        minutes = int(minutes // 60)
        return f"{hours}:{minutes:02}:{seconds:05.2f}"

    @property
    def ticks_per_beat(self):
        if len(self.time_signatures) < 1:
            return 0
        return (self.division * 4) / self.time_signature.numerator

    @property
    def time_signature(self):
        """
        The current time signature based on the absolute tick count in the track
        """
        try:
            # Use dict comprehension to find the index of the current timesignature where the index is
            # the highest value that is less than or equal to the current absolute tick location.
            return self.time_signatures[max({k for k in self.time_signatures if k <= self.absolute_ticks})]
        except ValueError:
            # A value error will occur on the max function when the current position is less than the first
            # index value meaning there is no entry for this position.
            pass
        return None

    @property
    def tempo(self):
        """
        The current tempo based on the absolute tick count in the track
        """
        try:
            # Use dict comprehension to find the index of the current tempo where the index is
            # the highest value that is less than or equal to the current absolute tick location.
            return self.tempos[max({k for k in self.tempos if k <= self.absolute_ticks})]
        except ValueError:
            # A value error will occur on the max function when the current position is less than the first
            # index value meaning there is no entry for this position.
            pass
        return 0

    def set_time_signature(self, time_signature, ticks=None):
        if ticks is None:
            ticks = self.measure_ticks
        self.time_signatures[ticks] = time_signature

    def update_ticks(self, delta_ticks: int):

        self.measure_ticks += delta_ticks
        self.absolute_ticks += delta_ticks

        time_signature = self.time_signature
        if time_signature is not None:

            ticks_per_beat = (self.division * 4) / time_signature.numerator

            # Calculate the number of beats to add
            self.measure_beats += (self.measure_ticks // ticks_per_beat)

            # Set the ticks to the new remainder
            self.measure_ticks = self.measure_ticks % ticks_per_beat

            # Calculate the number of measures to add
            self.measures += (self.measure_beats // time_signature.denominator)

            # Remove beats added to the measure
            self.measure_beats = (self.measure_beats % time_signature.denominator)

        tempo = self.tempo
        if tempo > 0:
            delta_quarter_notes = delta_ticks / self.division
            delta_seconds = (tempo / 1000000) * delta_quarter_notes
            self.absolute_seconds += delta_seconds

    def update_event(self, event: TrackEvent):

        self.update_ticks(event.delta_ticks)

        if event.time_signature:
            self.time_signatures[self.absolute_ticks] = event.time_signature
        elif event.tempo:
            self.tempos[self.absolute_ticks] = event.tempo
