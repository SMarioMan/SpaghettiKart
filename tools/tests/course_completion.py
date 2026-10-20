"""GDB-side driver, launched by run_course_completion.py (not imported normally)."""
import json
import os
from pathlib import Path
import time
import subprocess
import math
import signal
import gdb

config = json.loads(Path(os.environ['KART_COMPLETION_CONFIG']).read_text())
output = Path(config['output'])
players = config['players']
human = config.get('human_controls', False)
handoff = 780 if human else 280
report = {'players': players, 'race_driver': 'native CPU steering with human viewports',
          'battle_driver': 'human input and rescue, followed by scripted balloon damage' if human else 'scripted normal balloon damage entry point',
          'human_controls': human, 'requested_interpolation_fps': config.get('interpolation_fps', 30), 'courses': []}
report['audio_instrumentation'] = 'shared audio API entries' if config.get('trace_all_audio') else 'native roulette sound call sites'


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


def check_controller_edges():
    for player in range(players):
        assert value('gControllerFive') != value(f'&gControllers[{player}]'), 'aggregate controller aliases a physical port'
        execute(f'set $savedPad = gControllerPads[{player}]')
        execute(f'set $savedController = gControllers[{player}]')
        execute(f'set gControllers[{player}].button = 0')
        execute(f'set gControllers[{player}].stickDirection = 0')
        for buttons, stick, pressed, released, stick_pressed in (
                (40960, 70, 40960, 0, 256), (40960, 70, 0, 0, 0),
                (0, 0, 0, 40960, 0), (0, -70, 0, 0, 512), (0, 49, 0, 0, 0)):
            execute(f'set gControllerPads[{player}].button = {buttons}')
            execute(f'set gControllerPads[{player}].stick_x = {stick}')
            execute(f'set gControllerPads[{player}].stick_y = 0')
            execute(f'call update_controller({player})')
            assert value(f'gControllers[{player}].buttonPressed') == pressed, 'button repeats while held'
            assert value(f'gControllers[{player}].buttonDepressed') == released, 'button release lost'
            assert value(f'gControllers[{player}].stickPressed') == stick_pressed, 'stick edge/deadzone mismatch'
        execute(f'set gControllerPads[{player}] = $savedPad')
        execute(f'set gControllers[{player}] = $savedController')
    row['controller_edge_checks'] = players


row = None
frame = 0


class RouletteSound(gdb.Breakpoint):
    def __init__(self, line, stop_request=False):
        super().__init__(f'src/audio/external.c:{line}', internal=True)
        self.stop_request = stop_request
        self.silent = True
        self.condition = 'soundBits == 0x0100FE1C || soundBits == 0x0100FE47'

    def stop(self):
        if row is not None and 180 <= frame <= (450 if human else 280):
            player = value('arg0')
            sound = value('soundBits') & 0xffffffff
            if 0 <= player < players:
                key = None
                if sound == 0x0100FE1C:
                    key = 'roulette_stops' if self.stop_request else 'roulette_starts'
                elif sound == 0x0100FE47 and not self.stop_request:
                    key = 'award_sounds'
                if key:
                    row[key][player] += 1
        return False


class RouletteCall(gdb.Breakpoint):
    def __init__(self, call, key, player_expression):
        source = Path(gdb.decode_line('func_8007B34C')[1][0].symtab.fullname())
        lines = [number for number, text in enumerate(source.read_text().splitlines(), 1) if call in text]
        if len(lines) != 1:
            raise RuntimeError(f'expected one native roulette sound call: {call}')
        super().__init__(f'{source}:{lines[0]}', internal=True)
        self.key, self.player_expression = key, player_expression
        self.silent = True

    def stop(self):
        if row is not None and 180 <= frame <= (450 if human else 280):
            player = value(self.player_expression)
            assert 0 <= player < players, 'roulette sound belongs to an inactive player'
            row[self.key][player] += 1
        return False


execute('break thread5_iteration')
execute('run')
window = None
if not config.get('capture') and not config.get('video'):
    # Keep headless state matrices inexpensive; visual evidence uses 1280x720.
    execute('set $testWindow = (void*) SDL_GetWindowFromID(1)')
    if not value('$testWindow'):
        raise RuntimeError('SDL test window was not created')
    execute('call (void) SDL_SetWindowSize($testWindow, 640, 360)')
    report['window_size'] = [640, 360]
if config.get('capture') or config.get('video'):
    ids = subprocess.check_output(['xdotool', 'search', '--onlyvisible', '--pid',
                                   str(gdb.selected_inferior().pid)], text=True).split()
    window = ids[0]
    subprocess.run(['xdotool', 'windowsize', window, '1280', '720'], check=True)
    subprocess.run(['xdotool', 'windowmove', window, '0', '0'], check=True)
    report['window_size'] = [1280, 720]


def capture(index, label):
    if window and config.get('capture'):
        name = f'course-{index:02d}-{label}.png'
        subprocess.run(['import', '-window', window, str(output / name)], check=True)
        return name
    return None


execute(f'call CVarSetInteger("gInterpolationFPS", {config.get("interpolation_fps", 30)})')
execute('call CVarSetInteger("gVsyncEnabled", 0)')
video = None
video_log = None


def start_video(index):
    global video, video_log
    if config.get('video'):
        name = f'course-{index:02d}.mp4'
        video_log = (output / f'course-{index:02d}-video.log').open('w')
        video = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-f', 'x11grab',
                                  '-framerate', '120', '-video_size', '1280x720',
                                  '-i', os.environ['DISPLAY'] + '+0,0', '-c:v', 'libx264',
                                  '-preset', 'ultrafast', '-crf', '23', '-threads', '1',
                                  '-r', '120', '-fps_mode', 'cfr',
                                  str(output / name)], stdout=subprocess.DEVNULL, stderr=video_log)
        row['video'] = name


def stop_video():
    global video, video_log
    if video is not None:
        if video.poll() is None:
            video.send_signal(signal.SIGINT)
        try:
            status = video.wait(timeout=10)
        except subprocess.TimeoutExpired:
            video.kill()
            video.wait()
            raise RuntimeError('video recorder did not stop')
        finally:
            video = None
            video_log.close()
        if status not in (0, 255):
            raise RuntimeError(f'video recorder failed ({status})')


execute('delete breakpoints')
# Stop at the original invalid access, including calls made on the audio thread.
# Otherwise a recovering sanitizer could print a diagnostic yet finish the test.
for handler in ('__ubsan_handle_out_of_bounds', '__ubsan_handle_out_of_bounds_abort'):
    try:
        execute(f'info address {handler}')
        guard = gdb.Breakpoint(handler, internal=True)
        guard.silent = True
    except gdb.error:
        pass  # Normal builds do not link the sanitizer runtime.
frame_breakpoint = gdb.Breakpoint('race_logic_loop')
frame_breakpoint.silent = True
if config.get('trace_all_audio'):
    roulette_sounds = [RouletteSound(2955), RouletteSound(2967, stop_request=True)]
else:
    # Only stop at the three native sound calls. Trapping the shared API also
    # stops thousands of engine sounds during accelerated CPU completion.
    roulette_sounds = [RouletteCall('func_800C8F80(arg1, 0x0100FE1CU)', 'roulette_starts', 'arg1'),
                       RouletteCall('func_800C9018((u8) playerId, SOUND_ARG_LOAD(0x01, 0x00, 0xFE, 0x1C))', 'roulette_stops', 'playerId'),
                       RouletteCall('func_800C8F80((u8) playerId, SOUND_ARG_LOAD(0x01, 0x00, 0xFE, 0x47))', 'award_sounds', 'playerId')]
for sound in roulette_sounds:
    sound.enabled = False
failed = False
try:
    for course_number, index in enumerate(config['courses']):
        frame = 0
        row = {'index': index, 'mode': 'battle' if index >= 16 else 'race', 'status': 'running',
               'roulette_textures': [[] for _ in range(players)], 'awarded_items': [0] * players,
               'roulette_starts': [0] * players, 'roulette_stops': [0] * players,
               'award_sounds': [0] * players, 'roulette_captures': []}
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
        start_video(index)
        previous_positions = {}
        row['max_unassisted_step'] = [0.0] * players
        results_frame = None
        for frame in range(1, config['max_frames'] + 1):
            execute('continue')
            if not gdb.selected_inferior().threads():
                raise RuntimeError('game exited before results')
            # Do not mistake a signal stop for a completed frame.
            if 'race_logic_loop' not in gdb.newest_frame().name():
                raise RuntimeError(f'unexpected stop: {gdb.newest_frame().name()}')
            if human and 180 <= frame < 450:
                for player in range(players):
                    # Exercise the human physics path, never PLAYER_CPU.
                    execute(f'set gControllers[{player}].button = {49152 if 330 <= frame < 345 else 32768}')
                    execute(f'set gControllers[{player}].rawStickX = {35 if (frame // 45 + player) % 2 else -35}')
            if human and 300 <= frame < 305:
                execute(f'set gControllers[{players - 1}].button = gControllers[{players - 1}].button | 2')
            if human and frame == 301:
                assert value(f'gScreenContexts[{players - 1}].camera') == value(f'gScreenContexts[{players - 1}].lookBehindCamera'), 'highest port cannot look behind'
            if human and frame == 306:
                assert value(f'gScreenContexts[{players - 1}].camera') == value(f'gScreenContexts[{players - 1}].raceCamera'), 'rear-view camera did not release'
            if human and frame == 319:
                row['zoom_before'] = [value(f'D_80164678[gScreenContexts[{p}].raceCamera->cameraId]') for p in range(players)]
            if human and frame in (320, 322):
                execute(f'set gControllers[{players - 1}].buttonPressed = 8')
            if human and frame in (321, 323):
                execute(f'set gControllers[{players - 1}].buttonPressed = 0')
                zoom = [value(f'D_80164678[gScreenContexts[{p}].raceCamera->cameraId]') for p in range(players)]
                expected = list(row['zoom_before'])
                if frame == 321:
                    expected[-1] = 1 - expected[-1]
                assert zoom == expected, 'zoom button affected the wrong player camera'
                assert value(f'D_80164678[gScreenContexts[{players - 1}].lookBehindCamera->cameraId]') == zoom[-1], 'rear camera zoom does not match its player'
            if human and 180 <= frame <= handoff:
                for player in range(players):
                    kart = gdb.parse_and_eval(f'gPlayers[{player}]')
                    pos = tuple(float(kart['pos'][axis]) for axis in range(3))
                    rescue = int(kart['lakituProps']) & 15
                    assert all(math.isfinite(x) and abs(x) < 40000 for x in pos), f'player {player + 1} invalid position {pos}'
                    previous = previous_positions.get(player)
                    if previous and not rescue and not previous[1]:
                        jump = math.dist(pos, previous[0])
                        row['max_unassisted_step'][player] = max(row['max_unassisted_step'][player], jump)
                        assert jump < 100, f'player {player + 1} teleported {jump:.1f} units without rescue'
                    previous_positions[player] = (pos, rescue)
            if frame == 180:
                for sound in roulette_sounds:
                    sound.enabled = True
                execute('set $fiFrames = (int) GameEngine_GetInterpolationFrameCount()')
                row['interpolation_frames'] = value('$fiFrames')
                if human:
                    check_controller_edges()
                    execute('call CVarSetInteger("gLookBehind", 1)')
                assert row['interpolation_frames'] >= config.get('interpolation_fps', 30) // 30, 'requested interpolation rate was not exercised'
                indices = [value(f'gItemWindowObjectByPlayerId[{p}]') for p in range(players)]
                assert len(set(indices)) == players, 'players share an item-window object'
                row['camera_follow_offsets'] = [float(gdb.parse_and_eval(f'gScreenContexts[{p}].camera->unk_30[2]')) for p in range(players)]
                if players > 4:
                    assert all(offset <= -76 for offset in row['camera_follow_offsets']), 'extended camera too close'
                    assert all(float(gdb.parse_and_eval(f'gScreenContexts[{p}].camera->fieldOfView')) >= 59 for p in range(players)), 'narrow camera field of view'
                for player in range(players):
                    assert value(f'gScreenContexts[{player}].screenWidth') == (80 if players > 4 else 160), f'player {player + 1} viewport width'
                    assert value(f'gScreenContexts[{player}].screenHeight') == 120, f'player {player + 1} viewport height'
                if human:
                    # Move one existing box to each kart in turn; the real collision
                    # loop must break it and start that player's normal roulette.
                    execute('set $actorCount = (int) CM_GetActorSize()')
                    for actor in range(value('$actorCount')):
                        execute(f'set $box = CM_GetActor({actor})')
                        if value('$box->type') == value('ACTOR_ITEM_BOX'):
                            break
                    else:
                        raise RuntimeError('course has no native item box')
                    original = [float(gdb.parse_and_eval(f'$box->pos[{axis}]')) for axis in range(3)]
                    for player in range(players):
                        for axis in range(3):
                            execute(f'set $box->pos[{axis}] = gPlayers[{player}].pos[{axis}]')
                        execute('set $box->pos[0] = $box->pos[0] + 1')
                        execute('set $box->state = 2')
                        execute('set $box->flags = -16384')
                        execute('call evaluate_collision_for_players_and_actors()')
                        assert value('$box->state') == 3, f'player {player + 1} did not collect the box'
                        assert value(f'gObjectList[gItemWindowObjectByPlayerId[{player}]].state') == 1, f'player {player + 1} pickup missed HUD'
                    for axis in range(3):
                        execute(f'set $box->pos[{axis}] = {original[axis]}')
                else:
                    for player in range(players):
                        execute(f'call func_8007ABFC({player}, 0)')
                execute(f'set gTickLogic = {2 if human else 8}')
            if 180 <= frame <= (450 if human else 280):
                visible_textures, window_states = [], []
                for player in range(players):
                    obj = f'gObjectList[gItemWindowObjectByPlayerId[{player}]]'
                    texture = value(obj + '.textureListIndex')
                    visible_textures.append(texture)
                    window_states.append(value(obj + '.state'))
                    assert 0 <= texture <= 15, f'player {player + 1} invalid item texture {texture}'
                    if value(obj + '.state') >= 2:
                        assert value(obj + '.activeTexture') == value(f'gItemWindowTextures[{texture}]'), 'roulette texture does not match animated icon'
                        assert value(obj + '.activeTLUT') == value(f'gItemWindowTLUTs[{texture}]'), 'roulette palette does not match animated icon'
                    if texture not in row['roulette_textures'][player]:
                        row['roulette_textures'][player].append(texture)
                    item = value(f'gPlayers[{player}].currentItemCopy')
                    if item:
                        row['awarded_items'][player] = item
                if (config.get('capture') and len(row['roulette_captures']) < 2
                        and all(state in (3, 4, 5) for state in window_states)
                        and all(visible_textures)
                        and (not row['roulette_captures'] or all(
                            current != previous for current, previous in zip(
                                visible_textures, row['roulette_captures'][-1]['textures'])))):
                    screenshot = capture(index, f'roulette-{len(row["roulette_captures"])}')
                    row['roulette_captures'].append({'frame': frame, 'image': screenshot, 'textures': visible_textures})
            if frame == (450 if human else 280):
                assert all(len(textures) >= 8 for textures in row['roulette_textures']), 'roulette did not animate through native icons'
                assert all(row['awarded_items']), 'pickup never awarded an item without Z'
                assert row['roulette_starts'] == [1] * players, f'duplicate or missing roulette starts: {row["roulette_starts"]}'
                assert row['roulette_stops'] == [1] * players, f'roulette sound did not stop: {row["roulette_stops"]}'
                assert row['award_sounds'] == [1] * players, 'missing or duplicate item award sound'
                for sound in roulette_sounds:
                    sound.enabled = False
                if human:
                    for player in range(players):
                        execute(f'set gControllers[{player}].button = 0')
                        execute(f'set gControllers[{player}].rawStickX = 0')
                    row['used_item'] = value(f'gPlayers[{players - 1}].currentItemCopy')
                    assert row['used_item'], 'highest port has no usable award'
            if human and frame == 451:
                execute(f'set gControllers[{players - 1}].button = 8192')
                execute(f'set gControllers[{players - 1}].buttonPressed = 8192')
            if human and frame == 470:
                item = value(f'gPlayers[{players - 1}].currentItemCopy')
                boost = value(f'gPlayers[{players - 1}].effects') & 8192
                assert item != row['used_item'] or boost, 'highest-port item button did not use the awarded item'
            if human and index >= 16 and frame == 500:
                row['full_transition_before_rescue'] = value('gTransitionType[4]')
                for player in range(players):
                    execute('call ((void (*)(void*)) &func_80090868)'
                            f'((void*) &gPlayers[{player}])')
            if frame == handoff:
                if human and index >= 16:
                    if players > 4:
                        assert value('gTransitionType[4]') == row['full_transition_before_rescue'], 'rescue overwrote full-screen transition'
                        assert all(value(f'sExtendedRescueFade[{p}].type') == 6 for p in range(players)), 'rescue fade did not finish for every viewport'
                    row['rescue_positions'] = []
                    for player in range(players):
                        kart = gdb.parse_and_eval(f'gPlayers[{player}]')
                        assert not (int(kart['lakituProps']) & 15), f'player {player + 1} rescue never completed'
                        pos = [float(kart['pos'][axis]) for axis in range(3)]
                        assert abs(pos[0]) < 1200 and abs(pos[2]) < 1200, f'player {player + 1} rescue outside arena'
                        expected_floor = {16: 200, 17: 0, 18: 0, 19: 480}[index]
                        assert expected_floor - 15 < pos[1] < expected_floor + 60, f'player {player + 1} rescue below floor {pos}'
                        row['rescue_positions'].append(pos)
                    for player in range(4, players):
                        assert math.dist(row['rescue_positions'][player], row['rescue_positions'][player - 4]) > 20, 'paired rescues overlap'
                if index < 16:
                    for player in range(players):
                        execute(f'set gPlayers[{player}].type = gPlayers[{player}].type | 4096')
                    execute('set gTickLogic = 64')
            elimination_start = handoff + 20
            if index >= 16 and elimination_start <= frame < elimination_start + (players - 1) * 3:
                victim = (frame - elimination_start) // 3
                if value(f'gPlayerBalloonCount[{victim}]') >= 0:
                    execute('call ((void (*)(void*, signed char)) &pop_player_balloon)'
                            f'((void*) &gPlayers[{victim}], (signed char) {victim})')
            if config.get('capture') and frame in (200, 210, 240, 300, 350, 400, 450, 550, 780):
                row['screenshots'].append(capture(index, f'frame-{frame}'))
            if frame % 100 == 0:
                laps = [value(f'gLapCountByPlayerId[{p}]') for p in range(players)]
                row.update(frames=frame, laps=laps)
                save()
                print(f'COURSE {index} frame {frame} race state {value("gRaceState")} laps {laps}', flush=True)
            if human and frame < handoff:
                assert value('gRaceState') != 5, 'battle ended before movement/rescue checks finished'
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
                    if config.get('capture'):
                        row['screenshots'].append(capture(index, 'results'))
                    stop_video()
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
    try:
        stop_video()
    except Exception as video_error:
        print(f'Video capture failed: {video_error}', flush=True)
    row.update(status='failed', error=str(error), frames=frame)
    if gdb.selected_inferior().threads():
        for depth in range(3):
            try:
                print(execute(f'frame {depth}'), flush=True)
                print(execute('info locals'), flush=True)
            except gdb.error:
                break
    print(execute('thread apply all bt'), flush=True)
    save()
    print(f'FAIL: {error}', flush=True)
finally:
    report['status'] = 'failed' if failed else 'passed'
    save()
    if gdb.selected_inferior().threads():
        execute('kill')
    execute('quit 1' if failed else 'quit 0')
