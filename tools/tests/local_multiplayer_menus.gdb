set pagination off
set confirm off
set environment SDL_AUDIODRIVER dummy
set environment LIBGL_ALWAYS_SOFTWARE 1
break thread5_iteration
run
set gMenuSelection = 11
set gGamestateNext = 1
set gGamestate = 7
set gMenuFadeType = 0
delete breakpoints
set $frame = 0
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
if $frame == 160
set $i = 0
while $i < 8
set gControllers[$i].buttonPressed = 32768
set $i = $i + 1
end
end
if $frame == 161
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
if $frame == 170
set gControllers[0].buttonPressed = 32768
end
if $frame == 225
if gMenuSelection != 13 || gPlayerCount != 8
printf "FAIL: track select lost eight-player selection (menu %d)\n", gMenuSelection
quit 2
end
printf "PASS: eight players proceed to track selection\n"
quit
end
continue
end
continue
