; Fixed scene-owned strips: point planes0/2/3 and WIN plane1.
HUD_POINT0 equ 0
HUD_POINT2 equ 512
HUD_POINT3 equ 1024
HUD_GAMES equ 1536
HUD_BANK_SIZE equ 3072
        section square_score_data,bss,chip
hud_bank0: ds.b HUD_BANK_SIZE
hud_bank1: ds.b HUD_BANK_SIZE
hud_bank2: ds.b HUD_BANK_SIZE
hud_point_tiles: ds.b 6*32
hud_win_tile: ds.b 16
