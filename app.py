#!/usr/bin/env python3
"""Flask web app for removing image corners."""
import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_radius_arg(radius_str, size):
    """Parse radius from string (pixels or percentage)."""
    if radius_str.endswith('%'):
        try:
            p = float(radius_str[:-1]) / 100.0
        except ValueError:
            raise ValueError('Invalid percent for radius')
        return int(min(size) * p)
    try:
        return int(radius_str)
    except ValueError:
        raise ValueError('Radius must be integer pixels or percent (e.g. 12%)')

def apply_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """Apply rounded corners to image."""
    w, h = img.size
    if radius <= 0:
        return img.convert('RGBA')

    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)

    img = img.convert('RGBA')
    img.putalpha(mask)
    return img

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """Handle image processing and return preview."""
    # accept multiple files
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    previews = []
    radius_str = request.form.get('radius', '10%')

    import base64
    try:
        for file in files:
            if file.filename == '':
                continue
            if not allowed_file(file.filename):
                # skip invalid types
                continue

            img = Image.open(file.stream)
            w, h = img.size

            try:
                radius = parse_radius_arg(radius_str, (w, h))
            except ValueError:
                radius = int(min(w, h) * 0.10)

            out_img = apply_rounded_corners(img, radius)

            img_io = io.BytesIO()
            out_img.save(img_io, 'PNG')
            img_io.seek(0)

            img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

            filename = secure_filename(file.filename)
            output_filename = os.path.splitext(filename)[0] + '_rounded.png'

            previews.append({
                'preview': f'data:image/png;base64,{img_base64}',
                'filename': output_filename,
                'width': w,
                'height': h,
                'radius': radius
            })

        if not previews:
            return jsonify({'error': 'No valid image files uploaded'}), 400

        return jsonify({'success': True, 'previews': previews})

    except Exception as e:
        return jsonify({'error': f'Error processing images: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    """Handle image download after preview."""
    try:
        data = request.get_json()
        images = data.get('images') or []
        # images: list of {imageData, filename}
        if not images:
            return jsonify({'error': 'No images provided for download'}), 400

        # If only one image, return it directly
        import base64, zipfile

        if len(images) == 1:
            # support payloads where frontend used key 'preview' or 'imageData'
            img_data = images[0].get('imageData') or images[0].get('preview') or ''
            filename = images[0].get('filename', 'image_rounded.png')
            parts = img_data.split(',') if img_data else []
            if len(parts) < 2:
                return jsonify({'error': 'Invalid image data'}), 400
            img_bytes = base64.b64decode(parts[1])
            img_io = io.BytesIO(img_bytes)
            return send_file(
                img_io,
                mimetype='image/png',
                as_attachment=True,
                download_name=filename
            )

        # multiple images -> create zip
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for item in images:
                img_data = item.get('imageData') or item.get('preview') or ''
                filename = item.get('filename', 'image_rounded.png')
                try:
                    parts = img_data.split(',') if img_data else []
                    if len(parts) < 2:
                        continue
                    img_bytes = base64.b64decode(parts[1])
                except Exception:
                    continue
                zf.writestr(filename, img_bytes)
        zip_io.seek(0)
        return send_file(
            zip_io,
            mimetype='application/zip',
            as_attachment=True,
            download_name='images_rounded.zip'
        )

    except Exception as e:
        return jsonify({'error': f'Error downloading images: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
