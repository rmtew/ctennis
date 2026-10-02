"""Accepted PAL native cadence; not derived from cartridge or source captures."""
from fractions import Fraction

CCK_HZ = 3546895
ECLK_HZ = 709379
INTERVAL_WHOLE = 11838
INTERVAL_FRACTION = 14906
INTERVAL_16_16 = INTERVAL_WHOLE * 65536 + INTERVAL_FRACTION
INTERVAL_CCK = Fraction(INTERVAL_16_16 * 5, 65536)


def clock_contract():
    return {'eclock_hz': ECLK_HZ, 'cck_hz': CCK_HZ, 'cck_per_eclock': 5,
            'interval_16_16': INTERVAL_16_16, 'resolution_cck': 1,
            'origin_uncertainty_cck': 5,
            'interval_rounding_error_eclock': '<= N/(2*65536)',
            'rules': {'entry': 'not before native deadline minus quantization; before next deadline',
                      'completion': 'before next deadline',
                      'publication': 'court bank before PAL sprite DMA line25 or late blank >=252; latest completed prepared epoch',
                      'telemetry': 'zero missing, duplicate or dropped events',
                      'memory': 'validated Exec chip free list; continuously observe topology/free mutations',
                      'entropy': 'ordinary native timer; no phase or recorded entropy initialization'}}
