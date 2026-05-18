import os
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(file_obj, matric_number):
    """Save and resize student photo."""
    ext = file_obj.filename.rsplit('.', 1)[1].lower()
    filename = f"photo_{matric_number.replace('/', '_')}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    img = Image.open(file_obj)
    img = img.convert('RGB')
    img.thumbnail((400, 400), Image.LANCZOS)

    # Crop to square
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))
    img = img.resize((300, 300), Image.LANCZOS)
    img.save(filepath, quality=90)
    return filename

def format_matric(department_code, year, seq):
    """Format matric number: e.g. CSC/2021/045"""
    return f"{department_code.upper()}/{year}/{str(seq).zfill(3)}"

def get_dashboard_stats(app_context=None):
    """Get system statistics for dashboard."""
    from app.models.models import Student, ScanLog, User, Role, Staff
    from datetime import datetime, timedelta

    total_students = Student.query.count()
    active_cards = Student.query.filter_by(card_status='active').count()
    total_scans = ScanLog.query.count()
    total_staff = Staff.query.count()

    today = datetime.utcnow().date()
    today_scans = ScanLog.query.filter(
        ScanLog.scanned_at >= datetime.combine(today, datetime.min.time())
    ).count()

    recent_scans = ScanLog.query.order_by(ScanLog.scanned_at.desc()).limit(10).all()
    recent_students = Student.query.order_by(Student.registered_at.desc()).limit(5).all()

    return {
        'total_students': total_students,
        'active_cards': active_cards,
        'total_scans': total_scans,
        'total_staff': total_staff,
        'today_scans': today_scans,
        'recent_scans': recent_scans,
        'recent_students': recent_students,
    }
