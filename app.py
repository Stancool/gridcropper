import os
import io
import zipfile
import uuid
from flask import Flask, render_template, request, send_file, session
from PIL import Image

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
UPLOAD_FOLDER = 'temp_uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def split_image_to_zip(image_path, x_lines, y_lines, selected_indices=None):
    img = Image.open(image_path)
    width, height = img.size
    
    # x_lines and y_lines are expected to be percentages [0-100]
    x_coords = [0] + [int(p * width / 100) for p in sorted(x_lines)] + [width]
    y_coords = [0] + [int(p * height / 100) for p in sorted(y_lines)] + [height]
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        count = 1
        for i in range(len(y_coords)-1):
            for j in range(len(x_coords)-1):
                # If selected_indices is provided, only process those in the list
                # count is 1-based, matching the UI
                if selected_indices is None or len(selected_indices) == 0 or count in selected_indices:
                    left = x_coords[j]
                    upper = y_coords[i]
                    right = x_coords[j+1]
                    lower = y_coords[i+1]
                    
                    tile = img.crop((left, upper, right, lower))
                    
                    tile_io = io.BytesIO()
                    tile.save(tile_io, format='PNG')
                    tile_io.seek(0)
                    
                    zf.writestr(f"shot{count:03d}.png", tile_io.getvalue())
                count += 1
                
    memory_file.seek(0)
    return memory_file



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Save the file temporarily
    file_ext = os.path.splitext(file.filename)[1]
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_FOLDER, file_id + file_ext)
    file.save(temp_path)
    
    return {"file_id": file_id + file_ext}

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    file_id = data.get('file_id')
    x_lines = data.get('x_lines', [33.33, 66.66])
    y_lines = data.get('y_lines', [33.33, 66.66])
    selected_indices = data.get('selected_indices', [])
    
    temp_path = os.path.join(UPLOAD_FOLDER, file_id)
    if not os.path.exists(temp_path):
        return "File not found", 404
    
    try:
        # If exactly one tile is selected, return it as a PNG instead of a ZIP
        if len(selected_indices) == 1:
            img = Image.open(temp_path)
            width, height = img.size
            x_coords = [0] + [int(p * width / 100) for p in sorted(x_lines)] + [width]
            y_coords = [0] + [int(p * height / 100) for p in sorted(y_lines)] + [height]
            
            target_idx = selected_indices[0]
            count = 1
            for i in range(len(y_coords)-1):
                for j in range(len(x_coords)-1):
                    if count == target_idx:
                        left = x_coords[j]
                        upper = y_coords[i]
                        right = x_coords[j+1]
                        lower = y_coords[i+1]
                        tile = img.crop((left, upper, right, lower))
                        
                        img_io = io.BytesIO()
                        tile.save(img_io, format='PNG')
                        img_io.seek(0)
                        return send_file(
                            img_io,
                            mimetype='image/png',
                            as_attachment=True,
                            download_name=f'shot{target_idx:03d}.png'
                        )
                    count += 1

        zip_buffer = split_image_to_zip(temp_path, x_lines, y_lines, selected_indices)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='perfect_split.zip'
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/preview/<file_id>')
def preview(file_id):
    path = os.path.join(UPLOAD_FOLDER, file_id)
    return send_file(path)

if __name__ == '__main__':
    # Ensure templates folder exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(host='0.0.0.0', port=5000, debug=True)
