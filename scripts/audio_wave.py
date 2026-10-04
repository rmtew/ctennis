"""Read PCM and IEEE-float RIFF audio from native emulator tests."""
import array
import math
import struct
import sys


def read_wave(path):
    data = path.read_bytes()
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE' or int.from_bytes(data[4:8], 'little') + 8 != len(data):
        raise ValueError('Incomplete or unsupported WAV container')
    fmt, pcm, offset = None, None, 12
    while offset + 8 <= len(data):
        tag, size = struct.unpack_from('<4sI', data, offset)
        payload = data[offset + 8:offset + 8 + size]
        if len(payload) != size:
            raise ValueError('Truncated WAV chunk')
        if tag == b'fmt ':
            fmt = payload
        elif tag == b'data':
            pcm = payload
        offset += 8 + size + (size & 1)
    if fmt is None or pcm is None or len(fmt) < 16:
        raise ValueError('WAV format/data missing')
    kind, channels, rate, byte_rate, alignment, bits = struct.unpack_from('<HHIIHH', fmt)
    if kind == 0xfffe:
        if len(fmt) != 40 or fmt[26:40] != bytes.fromhex('000000001000800000aa00389b71'):
            raise ValueError('Unsupported extended WAV subtype')
        kind = int.from_bytes(fmt[24:26], 'little')
    if (kind, bits) not in ((1, 16), (3, 32)) or alignment != channels * bits // 8 or byte_rate != rate * alignment or len(pcm) % alignment:
        raise ValueError('Unsupported WAV encoding')
    values = array.array('h' if kind == 1 else 'f', pcm)
    if sys.byteorder != 'little':
        values.byteswap()
    return {'channels': channels, 'sample_rate': rate, 'sample_frames': len(pcm) // alignment,
            'encoding': 'pcm16' if kind == 1 else 'float32'}, values


def crossing_frequency(values, rate, channels, start_seconds, end_seconds):
    first, last = int(start_seconds * rate), int(end_seconds * rate)
    mono = [sum(values[index * channels:(index + 1) * channels]) / channels
            for index in range(first, min(last, len(values) // channels))]
    if len(mono) < 4 or not all(math.isfinite(value) for value in mono):
        raise ValueError('Insufficient/invalid audio samples')
    middle = (min(mono) + max(mono)) / 2
    edges = [index + (middle - a) / (b - a) for index, (a, b) in enumerate(zip(mono, mono[1:])) if a <= middle < b]
    return {'cycles': max(0, len(edges) - 1),
            'frequency_hz': rate * (len(edges) - 1) / (edges[-1] - edges[0]) if len(edges) >= 2 else None,
            'minimum': min(mono), 'maximum': max(mono), 'start_seconds': start_seconds, 'end_seconds': end_seconds}
