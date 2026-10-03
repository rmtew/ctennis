ui_menu_lines: dc.l ui_start,ui_mode,ui_help_menu
ui_pages: dc.l ui_help_lines,ui_control_lines,ui_credit_lines
ui_help_lines:
        dc.l ui_how,ui_help1,ui_help2,ui_help3,ui_help4,ui_help5,ui_help6,ui_help7
ui_control_lines:
        dc.l ui_controls,ui_control1,ui_control2,ui_control3,ui_control4,ui_control5,ui_control6
ui_credit_lines:
        dc.l ui_credits,ui_game_credit,ui_game_credit_wrap,ui_font_credit,ui_ai_credit
ui_font_credit: dc.b 'Font author unknown.',0
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
ui_help2: dc.b 'Action: serve when ready.',0
ui_help3: dc.b 'Hold action at contact.',0
ui_help4: dc.b 'Changes height and depth.',0
ui_help5: dc.b 'Points: 15/30/40/game.',0
ui_help6: dc.b 'Deuce: win two in a row.',0
ui_help7: dc.b 'Six games wins the match.',0
ui_control1: dc.b 'A: WASD MOVE / F ACTION',0
ui_control2: dc.b 'B: ARROWS / . ACTION',0
ui_control3: dc.b 'KEYPAD 8/4/2/6 / 0 ACTION',0
ui_control4: dc.b 'A JOYSTICK PORT 2',0
ui_control5: dc.b 'B JOYSTICK PORT 1',0
ui_control6: dc.b 'DEMO: ENTER CHOOSE, ESC EXIT',0
ui_page1: dc.b 'PAGE 1 / 4',0
ui_page2: dc.b 'PAGE 2 / 4',0
ui_page3: dc.b 'PAGE 3 / 4',0
ui_page_navigation: dc.b 'BACK    EXIT    NEXT',0
ui_credits: dc.b 'Credits',0
ui_game_credit: dc.b 'Based on Champion Tennis',0
ui_game_credit_wrap: dc.b 'SG-1000 / SC-3000.',0
ui_ai_credit: dc.b 'AI used via Sol-6.1.',0
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
ui_scoring: dc.b 'Scoring and rules',0
ui_move_label: dc.b 'Move to ball',0
ui_move_detail: dc.b 'Auto return',0
ui_serve_label: dc.b 'Serve',0
ui_serve_detail: dc.b 'Press action',0
ui_shot_label: dc.b 'Shot',0
ui_shot_detail: dc.b 'Hold at contact',0
ui_changes_label: dc.b 'Changes',0
ui_changes_detail: dc.b 'Height and depth',0
ui_points_label: dc.b 'Points',0
ui_points_detail: dc.b '15/30/40/game',0
ui_deuce_label: dc.b 'Deuce',0
ui_deuce_detail: dc.b 'Win two in a row',0
ui_match_label: dc.b 'Match',0
ui_match_detail: dc.b 'Win six games',0
ui_demo_label: dc.b 'Demo',0
ui_demo_detail: dc.b 'Left / right',0
ui_confirm_label: dc.b 'Confirm',0
ui_confirm_detail: dc.b 'Enter or action',0
ui_exit_label: dc.b 'Exit',0
ui_exit_detail: dc.b 'Escape',0
ui_a_label: dc.b 'A',0
ui_a_keys: dc.b 'WASD move / F action',0
ui_b_label: dc.b 'B',0
ui_b_keys: dc.b 'Arrows move / . action',0
ui_keypad_label: dc.b 'Keypad B',0
ui_keypad_move: dc.b '8/4/2/6 move',0
ui_keypad_action: dc.b '0 action',0
ui_a_joy_label: dc.b 'A joystick',0
ui_b_joy_label: dc.b 'B joystick',0
ui_port2_detail: dc.b 'Port 2 / Fire',0
ui_port1_detail: dc.b 'Port 1 / Fire',0
ui_pause_label: dc.b 'Pause / resume',0
ui_pause_detail: dc.b 'P or Esc',0
        even

ui_play_prose0: dc.b 'Press action to serve.',0
ui_play_prose1: dc.b 'Move close to the ball to',0
ui_play_prose2: dc.b 'return it automatically.',0
ui_play_prose3: dc.b 'Hold action as you return',0
ui_play_prose4: dc.b 'the ball:',0
ui_play_prose5: dc.b 'Near net: lower / deeper',0
ui_play_prose6: dc.b 'Far back: higher / shorter',0
        even

ui_rule_prose0: dc.b 'Points: 0, 15, 30, 40, game.',0
ui_rule_prose1: dc.b '40-all: win two in a row.',0
ui_rule_prose2: dc.b 'Win one: advantage (A).',0
ui_rule_prose3: dc.b 'Win: game. Lose: 40-all.',0
ui_rule_prose4: dc.b 'First to six games wins.',0
ui_rule_prose5: dc.b 'Two serve faults lose point.',0
ui_rule_prose6: dc.b 'Return before second bounce.',0
        even

ui_a_compact: dc.b 'WASD / F',0
ui_a_joy_compact: dc.b 'Joystick (port 2) / Fire',0
ui_b_compact: dc.b 'Cursor keys / .',0
ui_keypad_compact: dc.b 'Keypad 8426 / 0',0
ui_b_joy_compact: dc.b 'Joystick (port 1) / Fire',0
        even
