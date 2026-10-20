# Local Versus and Battle for 5–8 players

On the main menu, press Right past 4P to choose 5P, 6P, 7P, or 8P.
The player count appears on the selected native menu card.
These additional counts offer Versus racing and Battle. Versus retains the existing
engine-class and mirror options. The original 1–4 player modes remain available.

Open the Input Editor in the port menu to configure Controllers 1–8. Assign a
separate gamepad to each port using the editor's device selection and default
mappings. Additional ports start without keyboard bindings, so they do not all
respond to player one's keys. Mappings use the existing saved configuration.

On character select, each player moves their own cursor and presses A to ready
or B to cancel. With more than four players, unconfirmed cursors can share a
character; confirming reserves it when unique character selection is enabled.
This allows all eight characters to be chosen without trapping eight cursors
on a full grid. Press A again once everyone is ready to continue to track select.

All extended counts use four columns and two rows with no added dividers. Unused
cells are black. On a 16:9 display each pane is 8:9; the engine preserves scene
proportions within the panes. Every active view has its own
camera with the original HUD textures and fonts for player number, position, lap,
and held item. Battle omits racing information and retains the native kart
balloons. Any active player can pause; the pause menu can be controlled by any player. Extended races
finish when all but one player have crossed the finish line, with a standings
panel and the existing retry/change-track/change-character/quit choices.

Battle uses all four original arenas, with paired starts at each native spawn
anchor. Players lose balloons and become bombs as in the original game; the last
survivor wins.

Grand Prix and Time Trials retain their original player limits. The
extended Versus mode uses the eight-racer Grand Prix item distribution and the
original four-listener audio mix.

## Build and checks

Follow [BUILDING.md](BUILDING.md) for native prerequisites, CMake configuration,
and ROM extraction. Build the game and the ROM-independent regression test:

```sh
cmake --build build --target Spaghettify local-multiplayer-layout-test --parallel 4
ctest --test-dir build --output-on-failure -R '^local-multiplayer-layout$'
```

The regression test checks bounds, overlap, and full canvas coverage for every
extended layout, including unused cells for five, six, and seven players.

Runtime testing should cover 5, 6, 7, and 8 players, plus original 1P and 4P modes:
select characters, start a race, drive and steer independently, collect and use
items on ports 5–8, pause/resume, finish, retry, change tracks, and return to the
menus. Also check a course with a Lakitu rescue and a second race with fewer
players. Gameplay requires a supported US ROM or a previously extracted
`mk64.o2r`; neither belongs in Git.

The input editor's two fixed four-port loops are adapted in generated build
sources by `cmake/LocalMultiplayer.cmake`. The pinned libultraship checkout stays
unchanged; configuration fails if those upstream assumptions change.

The Linux runtime smoke scripts can also be run with GDB against a Debug build,
from the build directory (a display or Xvfb and extracted assets are required):

```sh
python3 ../tools/tests/run_local_multiplayer_smoke.py ./Spaghettify
```

These inject controller input and race completion state to exercise menu,
viewport, item, pause, results, retry, Battle elimination, and sky-horizon paths.
They complement physical controller playtesting; they do not replace it. The
runner requires every expected outcome and fails on a debugger signal, missing
result, or timeout. Use `--suite counts`, `--suite menus`, `--suite workflow`,
`--suite battle`, `--suite menus_battle`, `--suite sky`, or `--suite baseline` to
run an individual group.

## Autonomous course completion

The completion harness runs all 16 stock tracks and all four battle arenas with
5–8 player viewports. Use a Debug build with GDB, extracted game assets, and an
X display (Xvfb works):

```sh
DISPLAY=:99 python3 tools/tests/run_course_completion.py build/Spaghettify \
  --players 8 --output /tmp/kart-completion --capture
```

`--capture` additionally requires `xdotool` and ImageMagick's `import`; use an
isolated display so other windows do not obscure screenshots. It saves 16:9
images during roulette, driving, and results. JSON reports and debugger logs
are written to the output directory; failures produce a nonzero exit code.
Reports are replaced on each run, so use separate directories for comparisons.

`--courses 0,15,16,19` selects a subset. Indices follow cup order: Mushroom 0–3,
Flower 4–7, Star 8–11, Special 12–15, Battle 16–19. Repeat with `--players 5`,
`6`, and `7` to cover every extended player count. Per-course frame watchdogs
and an overall wall-clock timeout catch stalls rather than reporting success.

Every course exercises the normal item pickup entry point for every player and
requires multiple roulette textures and a nonempty awarded item. This isolates
HUD animation from item-box placement/collision; it does not claim to test
physical collection of every box. Races enable native CPU steering while
retaining human players, views, and HUDs, then accelerate logic ticks. The
harness never writes positions, lap counts, ranks, or race completion state;
it requires the normal penultimate-finisher transition and results screen.
Battle scenarios call the normal balloon damage entry point three times per
opponent, then require elimination, the surviving player's victory, and results.
They test arena lifecycle and damage handling, rather than autonomous weapon
combat. The report records the driving method explicitly.

Screenshots provide visual regression evidence; passing gameplay assertions
alone does not prove the absence of intermittent flicker. Physical controller
playtesting remains necessary for input feel and human camera preferences.
