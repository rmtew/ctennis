SCORE_PATCH_COUNT equ 22
score_patch_descriptors:
        dc.l score_cop_232_hi+2,score_cop_232_lo+2,score_pointer_table_232
        dc.w $0005
        dc.l score_cop_233_hi+2,score_cop_233_lo+2,score_pointer_table_233
        dc.w $0005
        dc.l score_cop_234_hi+2,score_cop_234_lo+2,score_pointer_table_234
        dc.w $0005
        dc.l score_cop_235_hi+2,score_cop_235_lo+2,score_pointer_table_235
        dc.w $0005
        dc.l score_cop_244_hi+2,score_cop_244_lo+2,score_pointer_table_244
        dc.w $ffff
        dc.l score_cop_245_hi+2,score_cop_245_lo+2,score_pointer_table_245
        dc.w $ffff
        dc.l score_cop_246_hi+2,score_cop_246_lo+2,score_pointer_table_246
        dc.w $ffff
        dc.l score_cop_247_hi+2,score_cop_247_lo+2,score_pointer_table_247
        dc.w $ffff
        dc.l score_cop_point0_hi+2,score_cop_point0_lo+2,score_pointer_table_point0
        dc.w $fffe
        dc.l score_cop_point2_hi+2,score_cop_point2_lo+2,score_pointer_table_point2
        dc.w $fffe
        dc.l score_cop_point3_hi+2,score_cop_point3_lo+2,score_pointer_table_point3
        dc.w $fffe
        dc.l score_cop_point_restore0_hi+2,score_cop_point_restore0_lo+2,score_pointer_table_point_restore0
        dc.w $ffff
        dc.l score_cop_point_restore2_hi+2,score_cop_point_restore2_lo+2,score_pointer_table_point_restore2
        dc.w $ffff
        dc.l score_cop_point_restore3_hi+2,score_cop_point_restore3_lo+2,score_pointer_table_point_restore3
        dc.w $ffff
        dc.l score_cop_games_hi+2,score_cop_games_lo+2,score_pointer_table_games
        dc.w $fffe
        dc.l score_cop_120_hi+2,score_cop_120_lo+2,score_pointer_table_120
        dc.w $0004
        dc.l score_cop_122_hi+2,score_cop_122_lo+2,score_pointer_table_122
        dc.w $0004
        dc.l score_cop_123_hi+2,score_cop_123_lo+2,score_pointer_table_123
        dc.w $0004
        dc.l score_cop_224_hi+2,score_cop_224_lo+2,score_pointer_table_224
        dc.w $ffff
        dc.l score_cop_226_hi+2,score_cop_226_lo+2,score_pointer_table_226
        dc.w $ffff
        dc.l score_cop_227_hi+2,score_cop_227_lo+2,score_pointer_table_227
        dc.w $ffff
        dc.l score_cop_games_restore_hi+2,score_cop_games_restore_lo+2,score_pointer_table_games_restore
        dc.w $ffff
score_pointer_table_232: dc.l score_bank_mode_0_p0,score_bank_mode_1_p0,score_bank_mode_2_p0
score_pointer_table_233: dc.l score_bank_mode_0_p1,score_bank_mode_1_p1,score_bank_mode_2_p1
score_pointer_table_234: dc.l score_bank_mode_0_p2,score_bank_mode_1_p2,score_bank_mode_2_p2
score_pointer_table_235: dc.l score_bank_mode_0_p3,score_bank_mode_1_p3,score_bank_mode_2_p3
score_pointer_table_244: dc.l plane0+42*32
score_pointer_table_245: dc.l plane1+42*32
score_pointer_table_246: dc.l plane2+42*32
score_pointer_table_247: dc.l plane3+42*32
score_pointer_table_point0: dc.l hud_bank0+HUD_POINT0
score_pointer_table_point2: dc.l hud_bank0+HUD_POINT2
score_pointer_table_point3: dc.l hud_bank0+HUD_POINT3
score_pointer_table_point_restore0: dc.l plane0+64*32
score_pointer_table_point_restore2: dc.l plane2+64*32
score_pointer_table_point_restore3: dc.l plane3+64*32
score_pointer_table_games: dc.l hud_bank0+HUD_GAMES
score_pointer_table_120: dc.l score_bank_status_0_p0,score_bank_status_1_p0,score_bank_status_2_p0,score_bank_status_3_p0,score_bank_status_4_p0,score_bank_status_5_p0,score_bank_status_6_p0
score_pointer_table_122: dc.l score_bank_status_0_p2,score_bank_status_1_p2,score_bank_status_2_p2,score_bank_status_3_p2,score_bank_status_4_p2,score_bank_status_5_p2,score_bank_status_6_p2
score_pointer_table_123: dc.l score_bank_status_0_p3,score_bank_status_1_p3,score_bank_status_2_p3,score_bank_status_3_p3,score_bank_status_4_p3,score_bank_status_5_p3,score_bank_status_6_p3
score_pointer_table_224: dc.l plane0+104*32
score_pointer_table_226: dc.l plane2+104*32
score_pointer_table_227: dc.l plane3+104*32
score_pointer_table_games_restore: dc.l plane1+120*32
hud_status_plane1: dc.l score_bank_status_0_p1,score_bank_status_1_p1,score_bank_status_2_p1,score_bank_status_3_p1,score_bank_status_4_p1,score_bank_status_5_p1,score_bank_status_6_p1
