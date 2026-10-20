#!/usr/bin/env python3
"""Run all stock cups to results under GDB; see docs/8PLAYER.md."""
import argparse
import json
import os
import signal
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--players', type=int, choices=range(5, 9), default=8)
    parser.add_argument('--courses', default=','.join(map(str, range(20))),
                        help='Cup order: races 0-15, battle arenas 16-19')
    parser.add_argument('--output', type=Path, default=Path('course-completion-results'))
    parser.add_argument('--capture', action='store_true', help='Save PNG evidence (requires xdotool and ImageMagick)')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--max-frames', type=int, default=2500)
    args = parser.parse_args()
    try:
        courses = [int(value) for value in args.courses.split(',')]
    except ValueError:
        parser.error('--courses must contain comma-separated integers')
    if args.timeout < 1 or args.max_frames < 1:
        parser.error('--timeout and --max-frames must be positive')
    if not courses or len(set(courses)) != len(courses) or any(i not in range(20) for i in courses):
        parser.error('--courses must contain unique indices from 0 through 19')
    binary = args.binary.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = dict(players=args.players, courses=courses, output=str(output), max_frames=args.max_frames, capture=args.capture)
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    env = os.environ.copy()
    env.update(SHIP_HOME=str(binary.parent), SDL_AUDIODRIVER='dummy', LIBGL_ALWAYS_SOFTWARE='1',
               KART_COMPLETION_CONFIG=str(output / 'config.json'))
    script = Path(__file__).with_name('course_completion.py').resolve()
    report = output / 'report.json'
    report.write_text(json.dumps({'players': args.players, 'status': 'starting', 'courses': []}) + '\n')
    with (output / 'gdb.log').open('w') as log:
        process = subprocess.Popen(['gdb', '-batch', '-ex', 'set pagination off',
                                    '-ex', 'set confirm off', '-ex', f'source {script}', str(binary)],
                                   cwd=binary.parent, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            returncode = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            # Kill the debugger and its game, rather than leaving an orphaned renderer.
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            data = json.loads(report.read_text())
            data['status'] = 'timeout'
            report.write_text(json.dumps(data, indent=2) + '\n')
            print(f'FAIL: timed out; inspect {output / "gdb.log"}', file=sys.stderr)
            return 1
    data = json.loads(report.read_text()) if report.exists() else {'courses': []}
    passed = [row for row in data['courses'] if row['status'] == 'passed']
    print(f'{len(passed)}/{len(courses)} courses passed; evidence: {output}')
    return 0 if returncode == 0 and len(passed) == len(courses) else 1


if __name__ == '__main__':
    sys.exit(main())
