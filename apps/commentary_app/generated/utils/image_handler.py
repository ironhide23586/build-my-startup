import tempfile
from PIL import Image

TEMP_DIR = tempfile.gettempdir() + '/uploads/'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_image(file):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    safe_filename = secure_filename(file.filename)
    file_path = os.path.join(TEMP_DIR, safe_filename)
    file.save(file_path)
    return file_path

def cleanup_old_images(max_age_seconds):
    current_time = time.time()
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)

def validate_image_format(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False