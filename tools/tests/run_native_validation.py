#!/usr/bin/env python3
"""Run menu, completion, human-control, and interpolation regressions; keep all failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, default=Path('native-validation-results'))
    parser.add_argument('--quick', action='store_true', help='Smaller development subset; report records this explicitly')
    parser.add_argument('--capture', action='store_true', help='Save menu and course screenshots on an isolated X display')
    parser.add_argument('--video', action='store_true', help='Record displayed interpolation frames in the highest-count human case')
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    with binary.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    report = {'binary': str(binary), 'sha256': digest.hexdigest(),
              'scope': 'development subset' if args.quick else 'full matrix', 'status': 'running', 'cases': []}

    def save():
        temporary = output / 'report.json.tmp'
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(output / 'report.json')

    cases = [
        ('layout', ['ctest', '--test-dir', str(binary.parent), '--no-tests=error',
                    '--output-on-failure', '-R', '^local-multiplayer-layout$']),
        ('smoke', [sys.executable, str(scripts / 'run_local_multiplayer_smoke.py'), str(binary), '--timeout', '300']),
    ]

    def course_case(name, players, courses, fps, human=False, video=False):
        command = [sys.executable, str(scripts / 'run_course_completion.py'), str(binary),
                   '--players', str(players), '--courses', ','.join(map(str, courses)),
                   '--interpolation-fps', str(fps), '--output', str(output / name)]
        if human:
            command.append('--human-controls')
        if args.capture:
            command.append('--capture')
        if video and args.video:
            command.append('--video')
        cases.append((name, command))

    if args.quick:
        course_case('completion', 8, (0, 19), 60)
        course_case('human-8', 8, (19,), 120, human=True, video=True)
    else:
        course_case('completion', 8, range(20), 60)
        for players, fps in ((4, 30), (5, 30), (6, 60), (7, 60), (8, 120)):
            course_case(f'human-{players}', players, range(16, 20), fps, human=True, video=players == 8)
        course_case('human-races', 8, (0, 3, 8, 13, 15), 120, human=True)

    env = os.environ.copy()
    if args.capture:
        env['KART_MENU_CAPTURE'] = str(output / 'character-select.png')
    try:
        for name, command in cases:
            row = {'name': name, 'command': command, 'status': 'running'}
            report['cases'].append(row)
            save()
            print(f'RUN: {name}', flush=True)
            try:
                with (output / f'{name}.log').open('w') as log:
                    result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
                row.update(status='passed' if result.returncode == 0 else 'failed', exit_code=result.returncode)
            except OSError as error:
                row.update(status='failed', error=str(error))
            save()
            print(f'{row["status"].upper()}: {name}', flush=True)
    except KeyboardInterrupt:
        report['status'] = 'cancelled'
        save()
        return 130
    report['status'] = 'passed' if all(row['status'] == 'passed' for row in report['cases']) else 'failed'
    save()
    print(f'{report["status"].upper()}: {len(cases)} selected cases; report: {output / "report.json"}')
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
