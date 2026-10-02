; Native scoring owns the point/game cells, service mode and scoring stage.
; Presentation, gameplay and audio observations enter through the temporary ABI.
        rsset 0
S_STAGE rs.b 1
S_AI rs.b 1
S_OUTCOME rs.b 1
S_MODE rs.b 1
S_DISPLAY rs.b 1
        rs.b 1 ; reserved byte5
S_POINTS rs.b 2 ; one byte per player; even for CLR.W
S_GAMES rs.b 2 ; one byte per player
S_TIMER rs.b 1
S_AUDIO_COMPLETE rs.b 1
        rs.b 1 ; reserved byte12
S_LOWER_ANIMATION rs.b 1
S_UPPER_ANIMATION rs.b 1
S_FLIGHT rs.b 1
S_LOWER_PHASE rs.b 1
S_UPPER_PHASE rs.b 1
S_LOWER_Y rs.b 1
S_LOWER_X rs.b 1
S_UPPER_Y rs.b 1
S_UPPER_X rs.b 1
S_LOWER_IMAGE rs.b 1
S_UPPER_IMAGE rs.b 1
S_ROUND_GAME_A rs.b 1
S_ROUND_GAME_B rs.b 1
S_EVENT rs.b 1
        rs.b 1 ; reserved byte27
S_SIZE rs.b 0
S_IDLE equ 0
S_ACTIVE equ 1
S_POINT_PAUSE equ 2
S_GAME_PAUSE equ 3
S_WAIT_SOUND equ 4
S_EVENT_SOUND equ 0
S_EVENT_POSITIONS equ 1
