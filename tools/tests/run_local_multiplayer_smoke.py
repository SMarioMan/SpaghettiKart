#!/usr/bin/env python3
"""Run Linux game integration checks with injected input and explicit outcomes."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

EXPECTED = {
    "sky": ["PASS: sky clipping isolated across eight cameras", "PASS: sky horizon remains stable in every yaw quadrant across eight cameras"],
    "battle": [
        *[f"PASS: {count}-player battle arena {count-5}, all players and balloons active" for count in (5, 6, 7, 8)],
        "PASS: player eight wins after seven eliminations",
        "PASS: eight-player battle results",
    ],
    "counts": [f"SMOKE: {count} players, 360 frames" for count in (8, 7, 6, 5)],
    "baseline": [f"SMOKE: {count} players, 360 frames" for count in (4, 1)],
    "menus": [
        "PASS: main menu selects 5, 6, 7, 8 and stops at 8",
        "PASS: character cursor sounds only on movement",
        "PASS: all eight characters ready",
        "PASS: eight players proceed to track selection",
    ],
    "menus_battle": ["PASS: eight players select Battle and proceed to arena selection"],
    "workflow": [
        "PASS: player 8 pause and shared resume",
        "PASS: player 8 mushroom input",
        "PASS: eight-player result screen",
        "PASS: retry preserves eight players",
    ],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--suite", choices=["all", *EXPECTED], default="all")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds per suite")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    suites = list(EXPECTED) if args.suite == "all" else [args.suite]
    environment = os.environ.copy()
    environment.setdefault("SDL_AUDIODRIVER", "dummy")
    environment.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    environment["SHIP_HOME"] = str(binary.parent)
    for suite in suites:
        script = Path(__file__).resolve().parent / f"local_multiplayer_{suite}.gdb"
        try:
            result = subprocess.run(
                ["gdb", "-batch", "-x", str(script), str(binary)],
                cwd=binary.parent, env=environment, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=args.timeout,
            )
        except subprocess.TimeoutExpired as error:
            print(f"FAIL: {suite} exceeded {args.timeout}s", file=sys.stderr)
            if error.stdout:
                print(error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout)
            return 1
        missing = [message for message in EXPECTED[suite] if message not in result.stdout]
        if result.returncode or missing or "received signal" in result.stdout or "FAIL:" in result.stdout:
            print(result.stdout)
            print(f"FAIL: {suite}; missing results: {missing}", file=sys.stderr)
            return 1
        print(f"PASS: {suite} ({len(EXPECTED[suite])} required outcomes)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
