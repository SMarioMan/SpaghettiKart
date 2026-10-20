"""Check displayed roulette icons, independently of their game-state indexes."""
import numpy as np
from PIL import Image


def check_captures(report, output):
    checks = 0
    players = report['players']
    if players <= 4:
        return {'status': 'not applicable', 'checks': 0,
                'reason': 'Pixel regions target the extended HUD; native four-player controls retain their original geometry.'}
    for course in report['courses']:
        captures = course.get('roulette_captures', [])
        if len(captures) != 2:
            raise AssertionError(f"course {course['index']}: missing distinct roulette captures")
        previous = None
        changed = 0
        for capture in captures:
            with Image.open(output / capture['image']) as image:
                # Extended HUD positions are in the full-height canvas's pixel
                # scale, independent of viewport scene projection and aspect.
                scale = image.height / 240
                patches = []
                for player in range(players):
                    center_x = (player % 4 + 1) * image.width / 4 - 20 * scale
                    center_y = player // 4 * image.height / 2 + 19 * scale
                    box = tuple(round(value) for value in (
                        center_x - 10 * scale, center_y - 9 * scale,
                        center_x + 10 * scale, center_y + 9 * scale))
                    pixels = np.array(image.convert('RGB').crop(box), dtype=np.int16)
                    # Ignore the white window border: an empty black interior
                    # must fail even if textureListIndex advances correctly.
                    if (pixels.max(axis=2) > 50).mean() < 0.01:
                        raise AssertionError(f"course {course['index']} player {player + 1}: displayed item icon is empty")
                    checks += 1
                    patches.append(pixels)
                    if previous is not None and capture['textures'][player] != captures[0]['textures'][player]:
                        if np.abs(pixels - previous[player]).mean() <= 1:
                            raise AssertionError(f"course {course['index']} player {player + 1}: displayed roulette is frozen")
                        changed += 1
                        checks += 1
                previous = patches
        if changed != players:
            raise AssertionError(f"course {course['index']}: displayed changes checked for {changed}/{players} players")
    return {'status': 'passed', 'checks': checks}


def self_test():
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from PIL import ImageDraw
    report = {'players': 8, 'courses': [{'index': 0, 'roulette_captures': [
        {'image': 'first.png', 'textures': [1] * 8},
        {'image': 'second.png', 'textures': [2] * 8}]}]}
    with TemporaryDirectory() as directory:
        output = Path(directory)
        images = []
        for color in ('red', 'green'):
            image = Image.new('RGB', (640, 360))
            draw = ImageDraw.Draw(image)
            for player in range(8):
                x, y = (player % 4 + 1) * 160 - 30, player // 4 * 180 + 28.5
                draw.rectangle((x - 25, y - 20, x + 25, y + 20), outline='white', width=2)
                draw.rectangle((x - 5, y - 5, x + 5, y + 5), fill=color)
            images.append(image)
        images[0].save(output / 'first.png')
        images[1].save(output / 'second.png')
        assert check_captures(report, output)['checks'] == 24
        for failure in ('empty', 'frozen'):
            image = images[0].copy()
            if failure == 'empty':
                draw = ImageDraw.Draw(image)
                for player in range(8):
                    x, y = (player % 4 + 1) * 160 - 30, player // 4 * 180 + 28.5
                    draw.rectangle((x - 20, y - 16, x + 20, y + 16), fill='black')
            image.save(output / 'second.png')
            try:
                check_captures(report, output)
            except AssertionError as error:
                assert failure in str(error), error
            else:
                raise AssertionError(f'{failure} HUD incorrectly passed')
    print('PASS: changing icons, empty framed windows, and frozen roulette controls')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.report:
        print(json.dumps(check_captures(json.loads(args.report.read_text()), args.report.parent), indent=2))
    else:
        parser.error('a course report or --self-test is required')
