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
set gVersusResultCursorSelection = 10
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
set $finishRequested = 0
break race_logic_loop
commands
silent
set $frame = $frame + 1
set $i = 0
while $i < $players
set gControllers[$i].button = 32768
set $i = $i + 1
end
if $frame == 300
set gControllers[7].buttonPressed = 4096
end
if $frame == 301
if gIsGamePaused == 0
printf "FAIL: player 8 could not pause\n"
quit 2
end
end
if $frame == 302
set gControllerFive->buttonPressed = 4096
end
if $frame == 303
if gIsGamePaused != 0
printf "FAIL: combined controller could not resume\n"
quit 2
end
printf "PASS: player 8 pause and shared resume\n"
end
if $frame == 340
set gPlayers[7].effects = 0
set gPlayers[7].currentItemCopy = 12
set gObjectList[gItemWindowObjectByPlayerId[7]].type = 12
set gObjectList[gItemWindowObjectByPlayerId[7]].state = 8
set gControllers[7].buttonPressed = 8192
end
if $frame == 341
if (gPlayers[7].effects & 8192) == 0
printf "FAIL: player 8 mushroom input\n"
quit 2
end
printf "PASS: player 8 mushroom input\n"
end
if $frame == 500
set $finishRequested = 1
end
if $frame == 501
if gRaceState != 5
printf "FAIL: extended VS finish state %d\n", gRaceState
quit 2
end
set D_802BA038 = 0
end
if $frame == 520
if D_8015F894 != 2
printf "FAIL: result screen transition\n"
quit 2
end
printf "PASS: eight-player result screen\n"
end
if $frame == 540
set gControllerFive->buttonPressed = 32768
end
if $frame == 630
printf "SMOKE: %d players, %d frames, race state %d\n", $players, $frame, gRaceState
set $i = 0
while $i < $players
printf "P%d type=%x speed=%f viewport=%dx%d camera=%p\n", $i+1, gPlayers[$i].type, gPlayers[$i].speed, gScreenContexts[$i].screenWidth, gScreenContexts[$i].screenHeight, gScreenContexts[$i].camera
if gScreenContexts[$i].camera == 0 || (gPlayers[$i].type & 49152) != 49152
quit 2
end
set $i = $i + 1
end
if gRaceState >= 5
printf "FAIL: retry did not start a new race\n"
quit 2
end
printf "PASS: retry preserves eight players\n"
quit
end
continue
end
break func_8028EF28
commands
silent
if $finishRequested
set $i = 0
while $i < 7
set gPlayers[$i].lapCount = 2
set gLapCountByPlayerId[$i] = 3
set gPlayers[$i].currentRank = $i
set gGPCurrentRaceRankByPlayerId[$i] = $i
set gPlayerPositionLUT[$i] = $i
set $i = $i + 1
end
set gPlayerPositionLUT[7] = 7
set $finishRequested = 0
end
continue
end
continue
