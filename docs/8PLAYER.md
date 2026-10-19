# Local Versus for 5–8 players

On the main menu, press Right past 4P to choose 5P, 6P, 7P, or 8P.
The player count appears in the main-menu header and on the selected card.
These additional counts offer Versus racing, including the existing engine-class
and mirror options. The original 1–4 player modes remain available.

Open the Input Editor in the port menu to configure Controllers 1–8. Assign a
separate gamepad to each port using the editor's device selection and default
mappings. Additional ports start without keyboard bindings, so they do not all
respond to player one's keys. Mappings use the existing saved configuration.

On character select, each player moves their own cursor and presses A to ready
or B to cancel. With more than four players, unconfirmed cursors can share a
character; confirming reserves it when unique character selection is enabled.
This allows all eight characters to be chosen without trapping eight cursors
on a full grid. Press A again once everyone is ready to continue to track select.

Five and six players use two columns and three rows. Seven and eight use two
columns and four rows. Unused cells are blank. Every active view has its own
camera and shows the player number, race position, lap, and held item. Any active
player can pause; the pause menu can be controlled by any player. Extended races
finish when all but one player have crossed the finish line, with a standings
panel and the existing retry/change-track/change-character/quit choices.

Grand Prix, Time Trials, and Battle retain their original player limits. The
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
extended layout, including the blank cell for odd player counts.

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
viewport, item, pause, results, and retry paths. They complement physical
controller playtesting; they do not replace it. The runner requires every expected outcome and fails on a debugger signal,
missing result, or timeout. Use `--suite counts`, `--suite menus`, or
`--suite workflow` to run an individual group.
