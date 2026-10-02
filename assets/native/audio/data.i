native_audio_scores:
        dc.l native_audio_score_0
        dc.l native_audio_score_1
        dc.l native_fanfare_0
        dc.l native_fanfare_1
        dc.l native_audio_score_4
        dc.l native_audio_score_5
        dc.l native_fanfare_2
native_audio_score_0: incbin "assets/native/audio/score-0.bin"
native_audio_score_1: incbin "assets/native/audio/score-1.bin"
native_audio_score_4: incbin "assets/native/audio/score-4.bin"
native_audio_score_5: incbin "assets/native/audio/score-5.bin"
native_audio_periods: incbin "assets/native/audio/periods.bin"
native_audio_envelopes: incbin "assets/native/audio/envelopes.bin"
        include "assets/native/audio/fanfare.i"
