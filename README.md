# remove_corners

Small Python utility to remove (round) the corners of an image and save it as a PNG with transparency.

Usage

Install requirements:

```bash
pip install -r requirements.txt
```

Basic commands:

```bash
# Default: 10% corner radius
python remove_corners.py input.jpg

# Specify output and pixel radius
python remove_corners.py input.jpg output.png --radius 30

# Use percent for radius (e.g. 12% of min(width,height))
python remove_corners.py input.jpg output.png --radius 12%
```

Output

The script writes a PNG with transparent rounded corners. If you don't provide an output path, it will save next to the input file with the `.png` extension.
