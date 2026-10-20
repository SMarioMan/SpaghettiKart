#!/usr/bin/env python3
"""Find wide transient bars in captured 4x2 gameplay; candidates require visual review."""
import argparse
from collections import deque
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw


def scan(video, output):
    output.mkdir(parents=True, exist_ok=True)
    info = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=avg_frame_rate', '-of', 'json', str(video)], text=True))
    numerator, denominator = map(int, info['streams'][0]['avg_frame_rate'].split('/'))
    fps = numerator / denominator
    width, height = 640, 360
    command = ['ffmpeg', '-v', 'error', '-threads', '1', '-filter_threads', '1', '-i', str(video),
               '-vf', f'scale={width}:{height}', '-pix_fmt', 'rgb24',
               '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
    frames = deque(maxlen=9)
    candidates = []
    count = 0
    last_candidate = -120
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        while True:
            raw = process.stdout.read(width * height * 3)
            if not raw:
                break
            if len(raw) != width * height * 3:
                raise RuntimeError('truncated decoded video frame')
            frames.append(raw)
            count += 1
            if len(frames) < 9 or count - 5 - last_candidate < 8:
                continue
            if frames[4] == frames[0] or frames[4] == frames[8]:
                continue  # Debugger pauses produce long runs of identical frames.
            before, center, after = (np.frombuffer(frames[index], np.uint8).reshape(
                height, width, 3).astype(np.int16) for index in (0, 4, 8))
            # A flash differs strongly from both neighboring logic frames, while
            # those neighbors remain similar. Continuous camera motion is excluded.
            transient = ((np.max(np.abs(center - before), axis=2) > 80) &
                         (np.max(np.abs(center - after), axis=2) > 80) &
                         (np.max(np.abs(before - after), axis=2) < 45))
            panes = []
            for player in range(8):
                x, y = (player % 4) * 160, (player // 4) * 180
                # Upper scene, excluding the HUD item window and center progress.
                rows = transient[y + 45:y + 115, x + 4:x + 156].mean(axis=1)
                if np.count_nonzero(rows > 0.6) >= 3:
                    panes.append(player + 1)
            if panes:
                index = count - 5
                last_candidate = index
                name = f'frame-{index:06d}.png'
                Image.frombytes('RGB', (width, height), frames[4]).save(output / name)
                candidates.append({'frame': index, 'seconds': round(index / fps, 3),
                                   'players': panes, 'image': name})
        if process.wait() != 0:
            raise RuntimeError('ffmpeg could not decode video')
    if count < 9:
        raise RuntimeError('video contains too few frames')
    report = {'video': str(video), 'frames': count, 'fps': fps, 'candidates': candidates,
              'status': 'review required' if candidates else 'no wide transient bars detected',
              'limitations': 'Heuristic for wide brief bars only; scene cuts/effects can be candidates. Does not establish absence of all flicker.'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if candidates:
        selected = candidates[:24]
        sheet = Image.new('RGB', (640 * 3, 388 * ((len(selected) + 2) // 3)))
        draw = ImageDraw.Draw(sheet)
        for slot, candidate in enumerate(selected):
            x, y = slot % 3 * 640, slot // 3 * 388
            with Image.open(output / candidate['image']) as frame:
                sheet.paste(frame, (x, y))
            draw.text((x + 5, y + 364), f"{candidate['seconds']}s; players {candidate['players']}", fill='white')
        sheet.save(output / 'candidates.png')
    print(f"{video.name}: {count} frames scanned; {len(candidates)} candidates for review")
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path, nargs='?')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--self-test', action='store_true', help='Verify a transient red bar and a small-object control')
    args = parser.parse_args()
    if args.self_test:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, box_width in (('red-bar', 152), ('small-object', 20)):
            video = args.output / f'{name}.mp4'
            # Microsecond timestamp jitter reproduces x11grab's variable rate.
            # Decoding must preserve the 240 real frames, rather than inventing
            # frames at the container's potentially enormous r_frame_rate.
            effect = ("settb=1/1000000,setpts=PTS+mod(N\\,3)," +
                      f"drawbox=x=4:y=50:w={box_width}:h=30:color=red:t=fill:enable='between(t,1,1.02)'")
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            'color=c=gray:s=640x360:r=120:d=2', '-vf', effect,
                            '-c:v', 'libx264', '-threads', '1', '-enc_time_base', '1:1000000',
                            '-fps_mode', 'passthrough', str(video)], check=True)
            result = scan(video.resolve(), args.output / name)
            assert result['frames'] == 240, 'variable-rate recording was resampled'
            assert bool(result['candidates']) == (name == 'red-bar'), result
            if name == 'red-bar':
                assert all(candidate['players'] == [1] for candidate in result['candidates'])
        print('PASS: red-bar detection and small-object control')
    elif args.video:
        scan(args.video.resolve(strict=True), args.output.resolve())
    else:
        parser.error('a video or --self-test is required')
