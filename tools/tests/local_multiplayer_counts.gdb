set $players = 8
set pagination off
set confirm off
set breakpoint pending on
set environment SDL_AUDIODRIVER dummy
set environment LIBGL_ALWAYS_SOFTWARE 1
break thread5_iteration
run
set gPlayerCount = $players
set gPlayerCountSelection1 = $players
set gScreenModeSelection = 3
set gModeSelection = 2
set gCCSelection = 2
set gDemoMode = 0
set gGamestateNext = 4
set gGamestate = 0
set gCharacterSelections[0] = 0
set gCharacterSelections[1] = 1
set gCharacterSelections[2] = 2
set gCharacterSelections[3] = 3
set gCharacterSelections[4] = 4
set gCharacterSelections[5] = 5
set gCharacterSelections[6] = 6
set gCharacterSelections[7] = 7
delete breakpoints
set $frame = 0
break race_logic_loop
commands
silent
set $frame = $frame + 1
set $i = 0
while $i < $players
set gControllers[$i].button = 32768
set $i = $i + 1
end
if $frame == 360
printf "SMOKE: %d players, %d frames, race state %d\n", $players, $frame, gRaceState
set $i = 0
while $i < $players
printf "P%d type=%x speed=%f viewport=%dx%d camera=%p\n", $i+1, gPlayers[$i].type, gPlayers[$i].speed, gScreenContexts[$i].screenWidth, gScreenContexts[$i].screenHeight, gScreenContexts[$i].camera
if gScreenContexts[$i].camera == 0 || (gPlayers[$i].type & 49152) != 49152
quit 2
end
set $i = $i + 1
end
if $players == 8
end
if $players == 5
quit
end
set $players = $players - 1
set gPlayerCount = $players
set gPlayerCountSelection1 = $players
set gGamestate = 0
set gGamestateNext = 4
set $frame = 0
end
continue
end
continue
