ui_menu_lines: dc.l ui_start,ui_mode,ui_help_menu,ui_controls
ui_pages: dc.l ui_help_lines,ui_control_lines,ui_credit_lines
ui_help_lines:
        dc.l ui_how,ui_help1,ui_help2,ui_help3,ui_help4,ui_help5,ui_help6,ui_help7
ui_control_lines:
        dc.l ui_controls,ui_control1,ui_control2,ui_control3,ui_control4,ui_control5,ui_control6
ui_credit_lines:
        dc.l ui_credits,ui_copyright,ui_version,ui_colours,ui_pause_hint,ui_font_credit,ui_font_archive
ui_font_credit: dc.b 'Font-Mac - creator unknown',0
ui_font_archive: dc.b 'Archive: ianhan/BitmapFonts',0
ui_start: dc.b 'Start',0
ui_mode: dc.b 'Mode',0
ui_help_menu: dc.b 'Help',0
ui_role_human: dc.b 'Human',0
ui_role_ai: dc.b 'AI',0
ui_how: dc.b 'How to play',0
ui_controls: dc.b 'Controls',0
ui_marker: dc.b '*',0
ui_empty: dc.b 0
ui_help1: dc.b 'Move to ball: auto return.',0
ui_help2: dc.b 'Either action: serve / shot.',0
ui_help3: dc.b 'At net: both actions lob.',0
ui_help4: dc.b 'At rear: both drop shot.',0
ui_help5: dc.b 'Points: 15/30/40/game.',0
ui_help6: dc.b 'Deuce: win two in a row.',0
ui_help7: dc.b 'Six games wins the match.',0
ui_control1: dc.b 'A: WASD MOVE / F OR G ACT',0
ui_control2: dc.b 'B: ARROWS / . OR / ACT',0
ui_control3: dc.b 'KEYPAD 8/4/2/6 / 0 OR . ACT',0
ui_control4: dc.b 'A JOYSTICK PORT 2',0
ui_control5: dc.b 'B JOYSTICK PORT 1',0
ui_control6: dc.b 'DEMO: ENTER CHOOSE, ESC EXIT',0
ui_page1: dc.b 'PAGE 1 / 4',0
ui_page2: dc.b 'PAGE 2 / 4',0
ui_page3: dc.b 'PAGE 3 / 4',0
ui_page_navigation: dc.b 'BACK    EXIT    NEXT',0
ui_credits: dc.b 'BASELINE RALLY / CREDITS',0
ui_copyright: dc.b 'SEGA-DERIVED / PRIVATE PORT',0
ui_version: incbin "build/native/version.bin"
ui_colours: dc.b 'A BLUE / B RED / B AI ROBOT',0
ui_pause_hint: dc.b 'P OR ESC: PAUSE / RESUME',0
ui_demo_selector: dc.b 'DEMO - TAKE OVER / EXIT',0
ui_blue_win: dc.b 'A WINS GAME',0
ui_red_win: dc.b 'B WINS GAME',0
ui_serve_text: dc.b 'YOUR SERVE',0
ui_tally_text: dc.b 'A '
ui_tally_blue_digit: dc.b '0'
        dc.b '  B '
ui_tally_red_digit: dc.b '0',0
ui_ai_win: dc.b 'B AI WINS GAME',0
ui_ai_tally_text: dc.b 'A '
ui_ai_tally_p1_digit: dc.b '0'
        dc.b '  B AI '
ui_ai_tally_p2_digit: dc.b '0',0
ui_paused_text: dc.b 'PAUSED',0
ui_confirm_text: dc.b 'RETURN TO TITLE?',0
ui_resume_text: dc.b 'RESUME',0
ui_return_text: dc.b 'RETURN TO TITLE',0
ui_no_text: dc.b 'NO - RESUME',0
ui_yes_text: dc.b 'YES - RETURN TO TITLE',0
ui_match_blue: dc.b 'A WINS  A '
ui_match_blue_a: dc.b '0'
        dc.b ' B '
ui_match_blue_b: dc.b '0',0
ui_match_red: dc.b 'B WINS  A '
ui_match_red_a: dc.b '0'
        dc.b ' B '
ui_match_red_b: dc.b '0',0
ui_match_continue: dc.b 'PRESS FIRE TO CONTINUE',0
        even

ui_page4: dc.b 'PAGE 4 / 4',0
ui_scoring: dc.b 'Scoring and demo',0
ui_move_label: dc.b 'Move',0
ui_move_detail: dc.b 'To ball:',0
ui_move_wrap: dc.b 'auto return',0
ui_action_label: dc.b 'Actions',0
ui_action_detail: dc.b 'Serve / shot',0
ui_net_label: dc.b 'At net',0
ui_net_detail: dc.b 'Both: lob',0
ui_contact_detail: dc.b 'at contact',0
ui_rear_label: dc.b 'At rear',0
ui_rear_detail: dc.b 'Both: drop',0
ui_points_label: dc.b 'Points',0
ui_points_detail: dc.b '15/30/40/game',0
ui_deuce_label: dc.b 'Deuce',0
ui_deuce_detail: dc.b 'Win two',0
ui_deuce_wrap: dc.b 'in a row',0
ui_match_label: dc.b 'Match',0
ui_match_detail: dc.b 'Win six games',0
ui_demo_label: dc.b 'Demo',0
ui_demo_detail: dc.b 'Left / right',0
ui_demo_wrap: dc.b 'Enter: choose',0
ui_help_demo_exit: dc.b 'Escape: exit',0
ui_a_label: dc.b 'A',0
ui_a_move: dc.b 'WASD move',0
ui_a_action: dc.b 'F or G action',0
ui_b_label: dc.b 'B',0
ui_b_move: dc.b 'Arrows move',0
ui_b_action: dc.b '. or / action',0
ui_keypad_label: dc.b 'Keypad B',0
ui_keypad_move: dc.b '8/4/2/6 move',0
ui_keypad_action: dc.b '0 or . action',0
ui_a_joy_label: dc.b 'A joystick',0
ui_b_joy_label: dc.b 'B joystick',0
ui_port2_detail: dc.b 'Port 2',0
ui_port1_detail: dc.b 'Port 1',0
        even
