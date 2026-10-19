set pagination off
set confirm off
set environment SDL_AUDIODRIVER dummy
set environment LIBGL_ALWAYS_SOFTWARE 1
break thread5_iteration
run
set $players = 5
set gPlayerCount = $players
set gPlayerCountSelection1 = $players
set gScreenModeSelection = 3
set gModeSelection = 3
set gDemoMode = 0
set gBattleResultCursorSelection = 10
call CM_SetCup(GetBattleCup())
call CM_SetCupIndex(4)
call SetCupCursorPosition(0)
call TrackBrowser_SetTrackFromCup()
set gGamestateNext = 4
set gGamestate = 0
set $i = 0
while $i < 8
set gCharacterSelections[$i] = $i
set $i = $i + 1
end
delete breakpoints
set $frame = 0
break race_logic_loop
commands
silent
set $frame = $frame + 1
if $frame == 175
# A stale balloon must be brought back to its kart by the normal update loop.
set $i = 0
while $i < $players
set gPlayerBalloonPosX[$i][0] = -30000
set $i = $i + 1
end
end
if $frame == 180
set $i = 0
while $i < $players
if gScreenContexts[$i].camera == 0 || (gPlayers[$i].type & 49152) != 49152 || gPlayerBalloonCount[$i] != 2
printf "FAIL: battle player %d not active with three balloons\n", $i+1
quit 2
end
if gPlayerBalloonPosX[$i][0] - gPlayers[$i].pos[0] > 20 || gPlayerBalloonPosX[$i][0] - gPlayers[$i].pos[0] < -20
printf "FAIL: player %d balloons do not follow the kart\n", $i+1
quit 2
end
if gScreenContexts[$i].screenWidth != 80 || gScreenContexts[$i].screenHeight != 120
printf "FAIL: battle viewport layout\n"
quit 2
end
set $i = $i + 1
end
printf "PASS: %d-player battle arena %d, all players and balloons active\n", $players, $players-5
end
if $frame == 185
# Exercise the normal hit/balloon-loss path on the highest controller port.
call ((void (*)(void*, signed char)) &pop_player_balloon)((void*) &gPlayers[$players-1], (signed char) ($players-1))
if gPlayerBalloonCount[$players-1] != 1
printf "FAIL: extended player cannot lose a balloon\n"
quit 2
end
end
if $frame == 190
if $players < 8
set $players = $players + 1
set gPlayerCount = $players
set gPlayerCountSelection1 = $players
call SetCupCursorPosition($players-5)
call TrackBrowser_SetTrackFromCup()
set gGamestate = 0
set gGamestateNext = 4
set $frame = 0
else
set $i = 0
while $i < 7
call ((void (*)(void*, signed char)) &pop_player_balloon)((void*) &gPlayers[$i], (signed char) ($i))
call ((void (*)(void*, signed char)) &pop_player_balloon)((void*) &gPlayers[$i], (signed char) ($i))
call ((void (*)(void*, signed char)) &pop_player_balloon)((void*) &gPlayers[$i], (signed char) ($i))
set $i = $i + 1
end
end
end
if $frame == 192
if gPlayerWinningIndex != 7 || gRaceState != 5
printf "FAIL: player eight did not win battle (winner %d, state %d)\n", gPlayerWinningIndex, gRaceState
quit 2
end
printf "PASS: player eight wins after seven eliminations\n"
end
if $frame == 230
if D_8015F894 != 2
printf "FAIL: battle results did not open\n"
quit 2
end
printf "PASS: eight-player battle results\n"
quit
end
continue
end
continue
