import struct

def create_midi_file(filename):
    # Header Chunk (Format 0, 1 Track, 480 Ticks Per Beat)
    header = b'MThd' + struct.pack('>IHHH', 6, 0, 1, 480)
    track_data = bytearray()
    
    # Time signature meta event (4/4 time)
    track_data.extend([0, 0xFF, 0x58, 0x04, 0x04, 0x02, 0x18, 0x08])
    
    # Program Change: Set to Orchestral String Ensemble (MIDI General Patch 48)
    track_data.extend([0, 0xC0, 48])
    
    # 20 Bars of 4-voice lush string arrangements
    progression = [
        [45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62], 
        [45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [40, 56, 59, 64], 
        [41, 57, 60, 65], [43, 59, 62, 67], [45, 57, 60, 64], [40, 55, 59, 64], 
        [41, 57, 60, 65], [43, 59, 62, 67], [48, 55, 60, 64], [47, 55, 59, 62], 
        [45, 57, 60, 64], [41, 57, 60, 65], [40, 56, 59, 64], [45, 57, 60, 69]  
    ]
    
    def write_varlen(value):
        buffer = bytearray()
        buffer.append(value & 0x7F)
        while value > 0x7F:
            value >>= 7
            buffer.insert(0, (value & 0x7F) | 0x80)
        return buffer

    ticks_per_bar = 1920
    
    for bar in progression:
        for i, note in enumerate(bar):
            track_data.extend(write_varlen(0))
            track_data.extend([0x90, note, 80]) # Note On
            
        for i, note in enumerate(bar):
            dt = 0 if i > 0 else ticks_per_bar
            track_data.extend(write_varlen(dt))
            track_data.extend([0x80, note, 64]) # Note Off
            
    track_data.extend([0, 0xFF, 0x2F, 0x00]) # End of track
    track_chunk = b'MTrk' + struct.pack('>I', len(track_data)) + track_data
    
    with open(filename, 'wb') as f:
        f.write(header + track_chunk)

create_midi_file('cinematic_strings_20bars.mid')
print("\n Done! 'cinematic_strings_20bars.mid' has been saved to your home folder.")
