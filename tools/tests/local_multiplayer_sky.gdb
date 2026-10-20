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
set $checked = 0
break race_logic_loop
commands
silent
set $frame = $frame + 1
if $frame == 300
enable 3 4
end
continue
end
break src/engine/sky/Sky.cpp:164
commands
silent
if $frame == 300
set $id = screen - gScreenContexts
set screen->camera->fieldOfView = 60
set screen->camera->lookAt[0] = screen->camera->pos[0] + (($id % 4 == 0) ? 10000 : (($id % 4 == 2) ? -10000 : 0))
set screen->camera->lookAt[1] = screen->camera->pos[1] - 100
set screen->camera->lookAt[2] = screen->camera->pos[2] + (($id % 4 == 1) ? 10000 : (($id % 4 == 3) ? -10000 : 0))
end
continue
end
break src/engine/sky/Sky.cpp:241
commands
silent
if $frame == 300
if screen->cameraHeight != 122
printf "FAIL: sky horizon depends on yaw or player world position (%d)\n", screen->cameraHeight
quit 2
end
# DrawFloor has restored the pane scissor before emitting its geometry.
set $clip = gDisplayListHead - 3
set $left = (screen->screenStartX - screen->screenWidth / 2) * 4
set $top = (screen->screenStartY - screen->screenHeight / 2) * 4
if (($clip->words.w0 >> 24) & 255) != 237 || (($clip->words.w0 >> 12) & 4095) != $left || ($clip->words.w0 & 4095) != $top
printf "FAIL: sky rendering escaped its player scissor\n"
quit 2
end
if (gDisplayListHead - 2)->words.w1 != 0 || ((gDisplayListHead - 1)->words.w0 & 255) != 0
printf "FAIL: sky inherited fill-cycle or textured state\n"
quit 2
end
set $checked = $checked + 1
if $checked == 8
printf "PASS: sky clipping isolated across eight cameras\n"
printf "PASS: sky horizon remains stable in every yaw quadrant across eight cameras\n"
quit
end
end
continue
end
disable 3 4
continue
