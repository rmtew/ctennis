; Native gameplay layout. No source-machine address or register ABI.
        rsset 0
P_PHASE rs.b 1
P_ANIMATION rs.b 1
P_Y rs.b 1
P_X rs.b 1
P_IMAGE rs.b 1
P_COLOUR rs.b 1
P_TARGET_Y rs.b 1
P_TARGET_X rs.b 1
P_CLOCK rs.b 1
P_STYLE rs.b 1 ; native colour role owned by logical player/end mapping
P_SIZE rs.b 0
        rsset 0
G_LOWER rs.b P_SIZE
G_UPPER rs.b P_SIZE
G_COURT_Y rs.b 1
G_COURT_X rs.b 1
G_SHADOW_COLOUR rs.b 1
G_FLIGHT rs.b 1
G_CONTACT rs.b 1
G_BALL_Y rs.b 1
G_BALL_X rs.b 1
G_BALL_IMAGE rs.b 1
G_BALL_COLOUR rs.b 1
G_LAUNCH_X rs.b 1
G_LAUNCH_Y rs.b 1
G_LAUNCH_Z rs.b 1
G_LAUNCH_SCREEN_Y rs.b 1
G_LAUNCH_BASE_X rs.b 1
G_LAUNCH_BASE_Y rs.b 1
G_TARGET_Y rs.b 1
G_TARGET_X rs.b 1
G_HEIGHT rs.b 1
G_VELOCITY_X rs.b 1
G_VELOCITY_Y rs.b 1
G_VELOCITY_Z rs.b 1
G_BASE_SCREEN_Y rs.b 1
G_BASE_X rs.b 1
G_BASE_Y rs.b 1
G_STEP rs.b 1
G_RANDOM rs.b 1
G_TICK rs.b 1
G_SERVE_CLOCK rs.b 1
G_ACTION_CLOCK rs.b 1
G_DISPLAY rs.b 1
G_LOWER_DIRECTION rs.b 1
G_UPPER_DIRECTION rs.b 1
G_LOWER_ACTION rs.b 1
G_UPPER_ACTION rs.b 1
G_LOWER_AI rs.b 1
G_UPPER_AI rs.b 1
G_TRACK_AI rs.b 1
G_FLIP_SERVE rs.b 1
G_SOUND_EVENT rs.b 1
        rs.b 1 ; reserved byte59
G_SIZE rs.b 0
