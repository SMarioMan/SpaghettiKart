set pagination off
set confirm off
set environment SDL_AUDIODRIVER dummy
set environment LIBGL_ALWAYS_SOFTWARE 1
break thread5_iteration
run
python
import os, subprocess
capture_path = os.environ.get('KART_MENU_CAPTURE')
if capture_path:
    window = subprocess.check_output(['xdotool', 'search', '--onlyvisible', '--pid', str(gdb.selected_inferior().pid)], text=True).split()[0]
    subprocess.run(['xdotool', 'windowsize', window, '1280', '720'], check=True)
    subprocess.run(['xdotool', 'windowmove', window, '0', '0'], check=True)
end
set gMenuSelection = 11
set gGamestateNext = 1
set gGamestate = 7
set gMenuFadeType = 0
delete breakpoints
set $frame = 0
set $cursorSounds = 0
set $okSounds = 0
break update_menus
commands
silent
set $frame = $frame + 1
if $frame >= 70 && $frame <= 84 && $frame % 2 == 0
set gControllers[0].buttonPressed = 256
end
if $frame == 85
if gPlayerCount != 8 || gPlayerCountSelection1 != 8
printf "FAIL: eight-player menu selection\n"
quit 2
end
printf "PASS: main menu selects 5, 6, 7, 8 and stops at 8\n"
end
if $frame == 90 || $frame == 100 || $frame == 110 || $frame == 120
set gControllers[0].buttonPressed = 32768
end
if $frame == 155
if gMenuSelection != 12
printf "FAIL: could not enter character select (menu %d)\n", gMenuSelection
quit 2
end
end
if $frame == 156
set gControllers[0].buttonPressed = 256
end
if $frame == 157
set gControllers[0].buttonPressed = 512
end
if $frame == 160
if $cursorSounds != 2
printf "FAIL: idle cursor sound or missing movement sound (%d)\n", $cursorSounds
quit 2
end
printf "PASS: character cursor sounds only on movement\n"
end
if $frame == 280
if $cursorSounds != 2 || gPlayerSelectMenuSelection != PLAYER_SELECT_MENU_MAIN
printf "FAIL: unready character cursors changed while idle\n"
quit 2
end
set $i = 0
while $i < 8
if gCharacterGridSelections[$i] != $i + 1
printf "FAIL: idle cursor moved on player %d\n", $i + 1
quit 2
end
set $i = $i + 1
end
printf "PASS: unready character cursors stay silent and stationary\n"
set $i = 0
while $i < 8
set gControllers[$i].buttonPressed = 32768
set $i = $i + 1
end
end
if $frame == 281
set $i = 0
while $i < 8
if !gCharacterGridIsSelected[$i]
printf "FAIL: player %d cannot ready\n", $i+1
quit 2
end
set $i = $i + 1
end
printf "PASS: all eight characters ready\n"
end
if $frame == 400
if $cursorSounds != 2 || $okSounds != 1
printf "FAIL: idle sound counts movement=%d OK=%d\n", $cursorSounds, $okSounds
quit 2
end
set $ok = find_menu_items_dupe(51)
if $ok->param1 != 0 || $ok->priority != 15 || $ok->column + 264 != 269 || $ok->row + 202 != 222
printf "FAIL: native OK prompt is hidden or covered\n"
quit 2
end
python
if capture_path:
    subprocess.run(['import', '-window', window, capture_path], check=True)
end
printf "PASS: native OK prompt and one announcement, no idle cursor sounds\n"
end
if $frame == 405
set gControllers[7].buttonPressed = 16384
end
if $frame == 406
if gCharacterGridIsSelected[7] || gPlayerSelectMenuSelection != PLAYER_SELECT_MENU_MAIN
printf "FAIL: player eight cannot cancel confirmation\n"
quit 2
end
end
if $frame == 410
set gControllers[7].buttonPressed = 32768
end
if $frame == 420
if !gCharacterGridIsSelected[7] || gPlayerSelectMenuSelection != PLAYER_SELECT_MENU_OK || $okSounds != 2 || $cursorSounds != 2
printf "FAIL: re-ready prompt or idle sound counts\n"
quit 2
end
printf "PASS: cancel and re-ready retains native confirmation\n"
end
if $frame == 430
set gControllers[0].buttonPressed = 32768
end
if $frame == 485
if gMenuSelection != 13 || gPlayerCount != 8
printf "FAIL: track select lost eight-player selection (menu %d)\n", gMenuSelection
quit 2
end
printf "PASS: eight players proceed to track selection\n"
quit
end
continue
end
break src/audio/external.c:2923
commands
silent
if $frame >= 155 && $frame < 430 && soundBits == 0x49008000
set $cursorSounds = $cursorSounds + 1
end
if $frame >= 155 && $frame < 430 && soundBits == 0x4900900f
set $okSounds = $okSounds + 1
end
continue
end
continue
