#!/usr/bin/env python3
"""Remove image corners (rounded) and save as PNG with transparency.

Usage examples:
  python remove_corners.py input.jpg
  python remove_corners.py input.jpg output.png --radius 30
  python remove_corners.py input.jpg output.png --radius 12%
"""
import argparse
import os
from PIL import Image, ImageDraw


def parse_radius_arg(radius_str, size):
    if radius_str.endswith('%'):
        try:
            p = float(radius_str[:-1]) / 100.0
        except ValueError:
            raise argparse.ArgumentTypeError('Invalid percent for radius')
        return int(min(size) * p)
    try:
        return int(radius_str)
    except ValueError:
        raise argparse.ArgumentTypeError('Radius must be integer pixels or percent (e.g. 12%)')


def apply_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    w, h = img.size
    if radius <= 0:
        return img.convert('RGBA')

    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)

    img = img.convert('RGBA')
    img.putalpha(mask)
    return img


def main():
    parser = argparse.ArgumentParser(description='Remove (round) image corners and save as PNG with transparency')
    parser.add_argument('input', help='Input image (e.g. JPG)')
    parser.add_argument('output', nargs='?', help='Output PNG path (defaults to input basename + .png)')
    parser.add_argument('--radius', '-r', default=None,
                        help='Corner radius in pixels or percent (e.g. 30 or 12%). Default is 10% of min(width,height)')

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        parser.error(f"Input file not found: {args.input}")

    img = Image.open(args.input)
    w, h = img.size

    if args.radius is None:
        radius = int(min(w, h) * 0.10)
    else:
        radius = parse_radius_arg(args.radius, (w, h))

    out_img = apply_rounded_corners(img, radius)

    out_path = args.output or (os.path.splitext(args.input)[0] + '.png')
    out_img.save(out_path, 'PNG')
    print(f'Saved -> {out_path}')


if __name__ == '__main__':
    main()
