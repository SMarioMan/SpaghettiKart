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
camera with the original HUD textures and fonts for position, lap, and held item.
The native shared race-progress portraits remain across the center of the screen.
Extended cameras use a wider field of view and a longer following distance. Battle omits racing information and retains the native kart
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
4–8 player viewports (four players provide a native control group). Use a Debug build with GDB, extracted game assets, and an
X display (Xvfb works):

```sh
DISPLAY=:99 python3 tools/tests/run_course_completion.py build/Spaghettify \
  --players 8 --output /tmp/kart-completion --capture
```

`--capture` additionally requires `xdotool`, ImageMagick's `import`, NumPy, and Pillow; use an
isolated display so other windows do not obscure screenshots. It saves 16:9
images during roulette, driving, and results. Extended HUD captures also check
that each item-window interior contains an icon and visibly changes between two
distinct roulette textures; native four-player controls retain their original HUD
geometry and are explicitly excluded from those extended pixel-region assertions. JSON reports and debugger logs
are written to the output directory; failures produce a nonzero exit code.
Reports are replaced on each run, so use separate directories for comparisons.

`--courses 0,15,16,19` selects a subset. Indices follow cup order: Mushroom 0–3,
Flower 4–7, Star 8–11, Special 12–15, Battle 16–19. Repeat with `--players 5`,
`6`, and `7` to cover every extended player count. Per-course frame watchdogs
and an overall wall-clock timeout catch stalls rather than reporting success.

Every course requires at least eight distinct native roulette icons and a nonempty
award without pressing Z. Breakpoints at the native roulette sound calls require exactly one start,
stop, and award notification per player. `--trace-all-audio` cross-checks the
same counts at the shared audio API entries; this costs more debugger stops. Each player must own a distinct
item-window object; requested interpolation rates and viewport sizes are checked. Races enable native CPU steering while
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

## Broader native-behavior regression matrix

Run the complete matrix with one command:

```sh
DISPLAY=:99 python3 tools/tests/run_native_validation.py build/Spaghettify \
  --output /tmp/kart-native-validation --capture
```

The matrix includes the layout test, all seven runtime smoke groups (27 required
outcomes), all 20 courses at eight players / 60 FPS, all four Battle arenas at
4, 5, 6, 7, and 8 players, and five representative races with human inputs at
120 FPS. The four-player Battle control group runs at 30 FPS; extended counts
cover 30, 60, and 120 FPS interpolation. `--quick` explicitly selects a smaller
development subset. `--video` records the highest-count human scenarios at 120 Hz
using ffmpeg, including displayed frames between game logic updates.
Course runs without captures use a 640×360 window; visual captures use 1280×720. Use an
isolated X display for captures and video. Reports include the executable SHA-256,
commands, per-case logs, course results, and failure details. Output directories
are replaced on reruns; use a fresh path to preserve comparisons.

Human-input scenarios can also be selected directly:

```sh
DISPLAY=:99 python3 tools/tests/run_course_completion.py build/Spaghettify \
  --players 8 --courses 16,17,18,19 --human-controls \
  --interpolation-fps 120 --capture --video --output /tmp/kart-human-battle
```

These first drive every kart through the human physics path at normal speed,
steer in both directions, brake, and hold/release the highest port's rear-view
button. They check camera zoom ownership and the raw-pad controller update path
for press, hold, release, both stick directions, and the deadzone. They move an existing native item box one unit beside each kart and run
the actual collision loop: the box must break and start that player's roulette.
They never inject held items, player positions, lap counts, or ranks. The highest
port must use its actual awarded item. Battle scenarios invoke native Lakitu
rescue for every port and check return to the arena floor, then apply scripted
balloon damage to finish. Position checks reject non-finite coordinates and
unexplained large per-frame teleports. Racing scenarios subsequently hand control
to native CPU steering to reach the real completion/results transition.

Menu regressions exercise real menu input, count movement sounds during idle
periods before and after confirming, cancel/re-ready the highest port, require one OK announcement per confirmation and a visible native OK prompt, and switch
Battle to VS without moving the track cursor to verify immediate preview refresh.
`--capture` saves the ready character-select screen as well as gameplay evidence.

For additional array-bounds coverage, enable instrumentation on a GCC/Clang Debug
build before running the same matrix:

```sh
cmake -S . -B build -DENABLE_MULTIPLAYER_BOUNDS_CHECKS=ON
cmake --build build --target Spaghettify local-multiplayer-layout-test --parallel 4
```

This instruments game C/C++ array access and enables libstdc++ container assertions.
The runners reject sanitizer diagnostics, signals, missing outcomes, and timeouts;
they preserve the failing debugger trace. This catches out-of-range controller,
audio, rescue-anchor, and fade-transition access that completion-only checks can
miss. It does not instrument the pinned libultraship dependency.

The collision fixture verifies every player's pickup path, rather than every box
placement on a course. Battle completion still uses scripted damage, rather than
autonomous weapon combat. Screenshots and video support review of HUD, camera,
cursors, and intermittent flashes; passing state assertions cannot establish that
every displayed frame is visually correct. Physical-controller play remains
necessary for input feel and camera preferences.

To scan a recording for wide transient bars, install NumPy and Pillow in the test
Python environment and run:

```sh
python3 tools/tests/scan_multiplayer_flashes.py /tmp/kart-human-battle/course-19.mp4 \
  --output /tmp/kart-flash-review
```

The scanner compares each displayed frame with neighboring logic frames and
saves candidate images, a contact sheet, and JSON timestamps/player panes. It
excludes the HUD and reports candidates for review, since legitimate scene cuts
and effects can also produce sudden changes. It does not certify that a video is
free of flicker. Run `--self-test --output /tmp/kart-scanner-fixtures` to verify a synthetic red
bar is detected and a small animated object is excluded. Both fixtures include
variable-rate timestamps and must decode to exactly their 240 recorded frames.

The HUD image checker can be rerun against a captured course report with
`python3 tools/tests/check_multiplayer_hud.py /tmp/kart-human-battle/report.json`.
Its `--self-test` verifies changing icons and rejects both empty framed windows
and frozen roulette images, independently of the game's texture-index counters.
