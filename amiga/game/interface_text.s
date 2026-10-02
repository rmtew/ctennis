ui_menu_lines: dc.l ui_start,ui_players_one,ui_how,ui_controls
ui_pages: dc.l ui_help_lines,ui_control_lines,ui_credit_lines
ui_help_lines:
        dc.l ui_how,ui_help1,ui_help2,ui_help3,ui_help4,ui_help5,ui_help6,ui_help7,ui_page1,ui_page_hint
ui_control_lines:
        dc.l ui_controls,ui_empty,ui_control1,ui_control2,ui_control3,ui_control4,ui_control5,ui_control6,ui_page2,ui_page_hint
ui_credit_lines:
        dc.l ui_credits,ui_copyright,ui_version,ui_colours,ui_empty,ui_pause_hint,ui_empty,ui_empty,ui_page3,ui_page_hint
ui_start: dc.b 'START GAME',0
ui_players_one: dc.b 'PLAYERS: 1',0
ui_players_two: dc.b 'PLAYERS: 2',0
ui_how: dc.b 'HOW TO PLAY',0
ui_controls: dc.b 'CONTROLS',0
ui_marker: dc.b '*',0
ui_menu_hint: dc.b 'UP/DOWN CHOOSE  ACTION OPEN',0
ui_empty: dc.b 0
ui_help1: dc.b 'MOVE TO BALL: AUTO RETURNS.',0
ui_help2: dc.b 'EITHER ACTION: SERVE / SHOT.',0
ui_help3: dc.b 'CONTACT, BOTH AT NET: LOB.',0
ui_help4: dc.b 'BOTH AT REAR: DROP SHOT.',0
ui_help5: dc.b 'POINTS: 15/30/40/GAME.',0
ui_help6: dc.b 'DEUCE: WIN 2 IN A ROW.',0
ui_help7: dc.b '6 GAMES WINS. TALLY: GAMES.',0
ui_control1: dc.b 'BLUE: WASD MOVE / F OR G ACT',0
ui_control2: dc.b 'RED: ARROWS / . OR / ACT',0
ui_control3: dc.b 'KEYPAD 8/4/2/6 / 0 OR . ACT',0
ui_control4: dc.b 'BLUE JOYSTICK PORT 2',0
ui_control5: dc.b 'RED JOYSTICK PORT 1',0
ui_control6: dc.b 'EITHER BUTTON: SERVE / SHOT',0
ui_page1: dc.b 'PAGE 1 / 3',0
ui_page2: dc.b 'PAGE 2 / 3',0
ui_page3: dc.b 'PAGE 3 / 3',0
ui_page_hint: dc.b 'LEFT/RIGHT PAGE ACTION EXIT',0
ui_credits: dc.b 'BASELINE RALLY / CREDITS',0
ui_copyright: dc.b 'SEGA-DERIVED / PRIVATE PORT',0
ui_version: incbin "build/native/version.bin"
ui_colours: dc.b 'BLUE AND RED KEEP CONTROLS.',0
ui_pause_hint: dc.b 'P OR ESC: PAUSE / RESUME',0
ui_demo_text: dc.b 'DEMO - G / PORT2 BUTTON2',0
ui_demo_hint: dc.b 'TAKE OVER BLUE / INPUT: MENU',0
ui_blue_win: dc.b 'BLUE WINS GAME',0
ui_red_win: dc.b 'RED WINS GAME',0
ui_serve_text: dc.b 'YOUR SERVE',0
ui_demo_blue_win: dc.b 'DEMO - BLUE WINS GAME',0
ui_demo_red_win: dc.b 'DEMO - RED WINS GAME',0
ui_demo_tally_text: dc.b 'BLUE'
ui_demo_tally_blue_digit: dc.b '0'
        dc.b ' RED'
ui_demo_tally_red_digit: dc.b '0'
        dc.b ' G/BTN2:TAKEOVER',0
ui_tally_text: dc.b 'BLUE '
ui_tally_blue_digit: dc.b '0'
        dc.b '  RED '
ui_tally_red_digit: dc.b '0',0
ui_paused_text: dc.b 'PAUSED',0
ui_confirm_text: dc.b 'RETURN TO TITLE?',0
ui_resume_text: dc.b 'RESUME',0
ui_return_text: dc.b 'RETURN TO TITLE',0
ui_no_text: dc.b 'NO - RESUME',0
ui_yes_text: dc.b 'YES - RETURN TO TITLE',0
ui_match_blue: dc.b 'BLUE WINS  BLUE '
ui_match_blue_a: dc.b '0'
        dc.b ' RED '
ui_match_blue_b: dc.b '0',0
ui_match_red: dc.b 'RED WINS   BLUE '
ui_match_red_a: dc.b '0'
        dc.b ' RED '
ui_match_red_b: dc.b '0',0
ui_match_continue: dc.b 'PRESS FIRE TO CONTINUE',0
        even
