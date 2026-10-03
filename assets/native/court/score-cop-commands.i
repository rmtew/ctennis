; Fixed full-width region changes; no per-row score/WIN pointer switching.
        dc.w $4e01,$fffe ; native y34, before first fetch
score_cop_232_hi: dc.w $00e0,0
score_cop_232_lo: dc.w $00e2,0
score_cop_233_hi: dc.w $00e4,0
score_cop_233_lo: dc.w $00e6,0
score_cop_234_hi: dc.w $00e8,0
score_cop_234_lo: dc.w $00ea,0
score_cop_235_hi: dc.w $00ec,0
score_cop_235_lo: dc.w $00ee,0
        dc.w $5601,$fffe ; native y42, before first fetch
score_cop_244_hi: dc.w $00e0,0
score_cop_244_lo: dc.w $00e2,0
score_cop_245_hi: dc.w $00e4,0
score_cop_245_lo: dc.w $00e6,0
score_cop_246_hi: dc.w $00e8,0
score_cop_246_lo: dc.w $00ea,0
score_cop_247_hi: dc.w $00ec,0
score_cop_247_lo: dc.w $00ee,0
        dc.w $5c01,$fffe ; native y48, before first fetch
score_cop_point0_hi: dc.w $00e0,0
score_cop_point0_lo: dc.w $00e2,0
score_cop_point2_hi: dc.w $00e8,0
score_cop_point2_lo: dc.w $00ea,0
score_cop_point3_hi: dc.w $00ec,0
score_cop_point3_lo: dc.w $00ee,0
        dc.w $6c01,$fffe ; native y64, before first fetch
score_cop_point_restore0_hi: dc.w $00e0,0
score_cop_point_restore0_lo: dc.w $00e2,0
score_cop_point_restore2_hi: dc.w $00e8,0
score_cop_point_restore2_lo: dc.w $00ea,0
score_cop_point_restore3_hi: dc.w $00ec,0
score_cop_point_restore3_lo: dc.w $00ee,0
        dc.w $7401,$fffe ; native y72, before first fetch
score_cop_games_hi: dc.w $00e4,0
score_cop_games_lo: dc.w $00e6,0
        dc.w $8c01,$fffe ; native y96, before first fetch
score_cop_120_hi: dc.w $00e0,0
score_cop_120_lo: dc.w $00e2,0
score_cop_122_hi: dc.w $00e8,0
score_cop_122_lo: dc.w $00ea,0
score_cop_123_hi: dc.w $00ec,0
score_cop_123_lo: dc.w $00ee,0
        dc.w $9401,$fffe ; native y104, before first fetch
score_cop_224_hi: dc.w $00e0,0
score_cop_224_lo: dc.w $00e2,0
score_cop_226_hi: dc.w $00e8,0
score_cop_226_lo: dc.w $00ea,0
score_cop_227_hi: dc.w $00ec,0
score_cop_227_lo: dc.w $00ee,0
        dc.w $a401,$fffe ; native y120, before first fetch
score_cop_games_restore_hi: dc.w $00e4,0
score_cop_games_restore_lo: dc.w $00e6,0
