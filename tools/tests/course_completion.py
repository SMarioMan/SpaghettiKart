"""GDB-side driver, launched by run_course_completion.py (not imported normally)."""
import json
import os
from pathlib import Path
import time
import subprocess
import gdb

config = json.loads(Path(os.environ['KART_COMPLETION_CONFIG']).read_text())
output = Path(config['output'])
players = config['players']
report = {'players': players, 'race_driver': 'native CPU steering with human viewports',
          'battle_driver': 'scripted normal balloon damage entry point', 'courses': []}


def execute(command):
    return gdb.execute(command, to_string=True)


def value(expression):
    return int(gdb.parse_and_eval(expression))


def save():
    temporary = output / 'report.json.tmp'
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(output / 'report.json')


def select_course(index):
    cup, slot = divmod(index, 4)
    name = ['Mushroom', 'Flower', 'Star', 'Special', 'Battle'][cup]
    execute(f'call CM_SetCup(Get{name}Cup())')
    execute(f'call CM_SetCupIndex({cup})')
    execute(f'call SetCupCursorPosition({slot})')
    execute('call TrackBrowser_SetTrackFromCup()')
    for expression, number in [('gPlayerCount', players), ('gPlayerCountSelection1', players),
                               ('gScreenModeSelection', 3), ('gModeSelection', 3 if cup == 4 else 2),
                               ('gCCSelection', 2), ('gDemoMode', 0), ('gTickLogic', 2),
                               ('gVersusResultCursorSelection', 10), ('gBattleResultCursorSelection', 10),
                               ('gGamestateNext', 4), ('gGamestate', 0)]:
        execute(f'set {expression} = {number}')
    for player in range(8):
        execute(f'set gCharacterSelections[{player}] = {player}')


execute('break thread5_iteration')
execute('run')
window = None
if config.get('capture'):
    ids = subprocess.check_output(['xdotool', 'search', '--onlyvisible', '--pid',
                                   str(gdb.selected_inferior().pid)], text=True).split()
    window = ids[0]
    subprocess.run(['xdotool', 'windowsize', window, '1280', '720'], check=True)
    subprocess.run(['xdotool', 'windowmove', window, '0', '0'], check=True)


def capture(index, label):
    if window:
        name = f'course-{index:02d}-{label}.png'
        subprocess.run(['import', '-window', window, str(output / name)], check=True)
        return name
    return None


execute('delete breakpoints')
frame_breakpoint = gdb.Breakpoint('race_logic_loop')
frame_breakpoint.silent = True
failed = False
try:
    for course_number, index in enumerate(config['courses']):
        frame = 0
        row = {'index': index, 'mode': 'battle' if index >= 16 else 'race', 'status': 'running',
               'roulette_textures': [[] for _ in range(players)], 'awarded_items': [0] * players}
        report['courses'].append(row)
        save()
        row['screenshots'] = []
        started = time.monotonic()
        if course_number:
            # Finish the old race frame before replacing its Track. Switching
            # inside race_logic_loop would tick new course objects before Init.
            frame_breakpoint.enabled = False
            boundary = gdb.Breakpoint('thread5_iteration', temporary=True, internal=True)
            boundary.silent = True
            execute('continue')
            if gdb.newest_frame().name() != 'thread5_iteration':
                raise RuntimeError('could not reach the course-transition boundary')
            frame_breakpoint.enabled = True
        select_course(index)
        results_frame = None
        for frame in range(1, config['max_frames'] + 1):
            execute('continue')
            if not gdb.selected_inferior().threads():
                raise RuntimeError('game exited before results')
            # Do not mistake a signal stop for a completed frame.
            if 'race_logic_loop' not in gdb.newest_frame().name():
                raise RuntimeError(f'unexpected stop: {gdb.newest_frame().name()}')
            if frame == 180:
                row['camera_follow_offsets'] = [float(gdb.parse_and_eval(f'gScreenContexts[{p}].camera->unk_30[2]')) for p in range(players)]
                assert all(offset <= -57 for offset in row['camera_follow_offsets']), 'extended camera too close'
                for player in range(players):
                    assert value(f'gScreenContexts[{player}].screenWidth') == 80, f'player {player + 1} viewport width'
                    assert value(f'gScreenContexts[{player}].screenHeight') == 120, f'player {player + 1} viewport height'
                    # Real pickup entry: no item, roulette, lap or completion state is injected.
                    execute(f'call func_8007ABFC({player}, 0)')
                execute('set gTickLogic = 8')
            if 180 <= frame <= 280:
                for player in range(players):
                    obj = f'gObjectList[gItemWindowObjectByPlayerId[{player}]]'
                    texture = value(obj + '.textureListIndex')
                    if texture not in row['roulette_textures'][player]:
                        row['roulette_textures'][player].append(texture)
                    item = value(f'gPlayers[{player}].currentItemCopy')
                    if item:
                        row['awarded_items'][player] = item
            if frame == 280:
                assert all(len(textures) >= 3 for textures in row['roulette_textures']), 'roulette did not animate'
                assert all(row['awarded_items']), 'pickup never awarded an item'
                if index < 16:
                    for player in range(players):
                        execute(f'set gPlayers[{player}].type = gPlayers[{player}].type | 4096')
                    execute('set gTickLogic = 64')
            if index >= 16 and frame >= 300 and frame < 300 + (players - 1) * 3:
                victim = (frame - 300) // 3
                execute('call ((void (*)(void*, signed char)) &pop_player_balloon)'
                        f'((void*) &gPlayers[{victim}], (signed char) {victim})')
            if window and frame in (200, 210, 240, 300, 350, 400):
                row['screenshots'].append(capture(index, f'frame-{frame}'))
            if frame % 100 == 0:
                laps = [value(f'gLapCountByPlayerId[{p}]') for p in range(players)]
                row.update(frames=frame, laps=laps)
                save()
                print(f'COURSE {index} frame {frame} race state {value("gRaceState")} laps {laps}', flush=True)
            if value('gRaceState') == 5:
                if results_frame is None:
                    results_frame = frame
                    row['laps'] = [value(f'gLapCountByPlayerId[{p}]') for p in range(players)]
                    if index < 16:
                        assert sum(lap >= 3 for lap in row['laps']) >= players - 1, 'finished before racers completed'
                    else:
                        assert value('gPlayerWinningIndex') == players - 1, 'wrong battle winner'
                        assert all(value(f'gPlayerBalloonCount[{p}]') < 0 for p in range(players - 1)), 'opponents not eliminated'
                if value('D_8015F894') == 2:
                    if window:
                        row['screenshots'].append(capture(index, 'results'))
                    row.update(status='passed', frames=frame, seconds=round(time.monotonic() - started, 2))
                    print(f'PASS: course {index} reached results', flush=True)
                    save()
                    break
            if results_frame and frame - results_frame > 200:
                raise RuntimeError('race finished but results did not open')
        else:
            raise RuntimeError('course exceeded frame watchdog')
except Exception as error:
    failed = True
    row.update(status='failed', error=str(error), frames=frame)
    print(execute('thread apply all bt'), flush=True)
    save()
    print(f'FAIL: {error}', flush=True)
finally:
    report['status'] = 'failed' if failed else 'passed'
    save()
    execute('kill')
    execute('quit 1' if failed else 'quit 0')
