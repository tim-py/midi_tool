"""
Contains the byte values for the midi data
"""

HEADER_INDICATOR = b'MThd'
TRACK_INDICATOR = b'MTrk'
END_OF_TRACK_INDICATOR = b'\xFF\x2F\x00'

CHANNEL_EVENTS = {0x80: "Note off",
                  0x90: "Note on",
                  0xA0: "Polyphonic Key Pressure",
                  0xB0: "Controller Change",
                  0xC0: "Program Change",
                  0xD0: "Channel Key Pressure",
                  0xE0: "Pitch Bend"}

META_EVENT_TYPES = {0x01: "Text",
                    0x02: "Copyright",
                    0x03: "Sequence/Track Name",
                    0x04: "Instrument Name",
                    0x05: "Lyric",
                    0x06: "Marker",
                    0x07: "Cue Point",
                    0x20: "MIDI Channel Prefix",
                    0x2F: "End of Track",
                    0x51: "Set Tempo",
                    0x54: "SMTPE Offset",
                    0x58: "Time Signature",
                    0x59: "Key Signature",
                    0x7F: "Sequencer-Specific Meta-event"}

CONTROLLER_MESSAGE = {0x00: 'Bank Select',
                      0x01: 'Modulation wheel',
                      0x02: 'Breath Control',
                      0x04: 'Foot controller',
                      0x05: 'Portamento time',
                      0x06: 'Data entry',
                      0x07: 'Channel Volume',
                      0x08: 'Balance',
                      0x0A: 'Pan',
                      0x0B: 'Expression controller',
                      0x0C: 'Effect control 1',
                      0x0D: 'Effect control 2',
                      0x10: 'General purpose controller #1',
                      0x11: 'General purpose controller #2',
                      0x12: 'General purpose controller #3',
                      0x13: 'General purpose controller #4',
                      0x20: 'Bank select',
                      0x21: 'Modulation wheel',
                      0x22: 'Breath control',
                      0x24: 'Foot controller',
                      0x25: 'Portamento time',
                      0x26: 'Data entry',
                      0x27: 'Channel volume',
                      0x28: 'Balance',
                      0x2A: 'Pan',
                      0x2B: 'Expression Controller',
                      0x2C: 'Effect control 1',
                      0x2D: 'Effect control 2',
                      0x30: 'General Purpose Controller #1',
                      0x31: 'General Purpose Controller #2',
                      0x32: 'General Purpose Controller #3',
                      0x33: 'General Purpose Controller #4',
                      0x40: 'Damper pedal on/off',
                      0x41: 'Portamento on/off',
                      0x42: 'Sustenuto on/off',
                      0x43: 'Soft pedal on/off',
                      0x44: 'Legato Footswitch',
                      0x45: 'Hold 2',
                      0x46: 'Sound ocntroller 1 (Sound Variation)',
                      0x47: 'Sound ocntroller 2 (Timbre)',
                      0x48: 'Sound ocntroller 3 (Release Time)',
                      0x49: 'Sound ocntroller 4 (Attack Time)',
                      0x4A: 'Sound ocntroller 5 (Brightness)',
                      0x4B: 'Sound ocntroller 6',
                      0x4C: 'Sound ocntroller 7',
                      0x4D: 'Sound ocntroller 8',
                      0x4E: 'Sound ocntroller 9',
                      0x4F: 'Sound ocntroller 10',
                      0x50: 'General Purpose Controller #5',
                      0x51: 'General Purpose Controller #6',
                      0x52: 'General Purpose Controller #7',
                      0x53: 'General Purpose Controller #8',
                      0x54: 'Portamento Control',
                      0x5B: 'Effects 1 Depth',
                      0x5C: 'Effects 2 Depth',
                      0x5D: 'Effects 3 Depth',
                      0x5E: 'Effects 4 Depth',
                      0x5F: 'Effects 5 Depth',
                      0x60: 'Data entry +1',
                      0x61: 'Data entry -1',
                      0x62: 'Non-registered parameter number LSB',
                      0x63: 'Non-registered parameter number MSB',
                      0x64: 'Registered parameter number LSB',
                      0x65: 'Registered parameter number MSB',
                      0x78: 'All sound off',
                      0x79: 'Reset all controllers',
                      0x7A: 'Local control on/off',
                      0x7B: 'All notes off',
                      0x7C: 'Omni mode off (+all notes off)',
                      0x7D: 'Omni mode on (+all notes off)',
                      0x7E: 'Poly mode on/off (+all notes off)',
                      0x7F: 'Poly mode on (incl mono=off +all notes off)'
                      }

CONTROLLER_ON_OFF = {0x40: {64: 'on', 63: 'off'},
                     0x41: {64: 'on', 63: 'off'},
                     0x42: {64: 'on', 63: 'off'},
                     0x43: {64: 'on', 63: 'off'},
                     0x44: {64: 'on', 63: 'off'},
                     0x45: {64: 'on', 63: 'off'},
                     0x7A: {127: 'on', 0: 'off'}
                     }

PROGRAMS = ['Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-Tonk Piano', # 1 - 4
            'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavi', # 5 - 8
            'Celeste', 'Glockenspiel', 'Music Box', 'Vibraphone',  # 9 - 12
            'Marimba', 'Xylophone', 'Tubular Bell', 'Dulimer',  # 13 - 16
            'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ',  # 17 - 20
            'Reed Organ', 'Accordion', 'Harmonica', 'Bandneon', # 21 - 24
            'Nylon-String Guitar', 'Steel-String Guitar', 'Jazz Guitar', 'Clean Guitar',  # 25 - 28
            'Muted Guitar', 'Overdriven Guitar', 'Distorted Guitar', 'Guitar Harmonics',  # 29 - 32
            'Acoustic Bass', 'Fingered Bass', 'Picked Bass', 'Fretless Bass',  # 33 - 36
            'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2',  # 37 - 40
            'Violin', 'Viola', 'Cello', 'Contrabass',   # 41 - 44
            'Tremelo Strings', 'Pizzicato Strings', 'Harp', 'Timpani',  # 45 - 48
            'Strings', 'Slow Strings', 'Synth Strings 1', 'Synth Strings 2',  # 49 - 52
            'Choral Ahs', 'Choral Oohs', 'Synth Vox', 'Orchastra Hit',  # 53 - 56
            'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet',   # 57 - 60
            'French Horn', 'Brass', 'Synth Brass 1', 'Synth Brass 2',  # 61 - 64
            'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax',  # 65 - 68
            'Oboe', 'English Horn', 'Bassoon', 'Clarinet',  # 69 - 72
            'Piccolo', 'Flute', 'Recorder', 'Pan Flute',   # 73 - 76
            'Bottle Blow', 'Shakuhachi', 'Whistle', 'Ocarina',  # 77 - 80
            'Square Wave', 'Sawtooth Wave', 'Synth Calliope', 'Chiffy Lead',  # 81 - 84
            'Charang', 'Solo Vox', 'Saw Wave Fifths', 'Brass & Lead',  # 85 - 88
            'Fantasia', 'Warm Pad', 'Polysynth', 'Space Voice',  # 89 - 92
            'Bowed Glass', 'Metal Pad', 'Halo Pad', 'Sweep Pad',  # 93 - 96
            'Ice Rain', 'Soundtrack', 'Crystal', 'Atmosphere',  # 97 - 100
            'Brightness', 'Goblin', 'Echo Drops', 'Star Theme', # 101 - 104
            'Sitar', 'Banjo', 'Shamisen', 'Koto',  # 105 - 108
            'Kalimba', 'Bagpipe', 'Kokyu', 'Shanai',  # 109 - 112
            'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', # 113 - 116
            'Taiko', 'Melow Tom', 'Synth Drum', 'Reverse Cymbal',  # 117 - 120
            'Guitar Fret Noise', 'Flanged Keyclick', 'Seashore', 'Bird',  # 121 - 124
            'Telephone', 'Helicopter', 'Applause', 'Gunshot']  # 125 - 128
