from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.models import User, Student, Staff, ScanLog, Role
from app.utils.qr_utils import decrypt_token, generate_id_card_image, generate_id_card_pdf
from datetime import datetime
import os

# ==================== STAFF ====================
staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [Role.STAFF, Role.ADMIN]:
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    staff = current_user.staff_profile
    my_scans = ScanLog.query.filter_by(scanned_by=current_user.id).order_by(ScanLog.scanned_at.desc()).limit(20).all()
    total_scans = ScanLog.query.filter_by(scanned_by=current_user.id).count()
    today = datetime.utcnow().date()
    today_scans = ScanLog.query.filter(
        ScanLog.scanned_by == current_user.id,
        ScanLog.scanned_at >= datetime.combine(today, datetime.min.time())
    ).count()
    return render_template('staff/dashboard.html', staff=staff, my_scans=my_scans,
                           total_scans=total_scans, today_scans=today_scans)

@staff_bp.route('/scanner')
@login_required
@staff_required
def scanner():
    return render_template('staff/scanner.html')

@staff_bp.route('/scan-logs')
@login_required
@staff_required
def scan_logs():
    logs = ScanLog.query.filter_by(scanned_by=current_user.id).order_by(ScanLog.scanned_at.desc()).all()
    return render_template('staff/scan_logs.html', logs=logs)

# ==================== STUDENT ====================
student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.STUDENT:
            flash('Student access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = current_user.student_profile
    if not student:
        flash('Student profile not found. Contact admin.', 'danger')
        return redirect(url_for('auth.logout'))
    scan_count = ScanLog.query.filter_by(student_id=student.id).count()
    return render_template('student/dashboard.html', student=student, scan_count=scan_count)

@student_bp.route('/id-card')
@login_required
@student_required
def id_card():
    student = current_user.student_profile
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    return render_template('student/id_card.html', student=student)

@student_bp.route('/download-card/<fmt>')
@login_required
@student_required
def download_card(fmt):
    student = current_user.student_profile
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('student.dashboard'))

    if fmt == 'pdf':
        filename = generate_id_card_pdf(student)
        filepath = os.path.join(current_app.config['IDCARD_FOLDER'], filename)
        return send_file(filepath, as_attachment=True,
                         download_name=f"ID_Card_{student.matric_number.replace('/', '_')}.pdf",
                         mimetype='application/pdf')
    else:
        filename = generate_id_card_image(student)
        filepath = os.path.join(current_app.config['IDCARD_FOLDER'], filename)
        return send_file(filepath, as_attachment=True,
                         download_name=f"ID_Card_{student.matric_number.replace('/', '_')}.png",
                         mimetype='image/png')

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    student = current_user.student_profile
    scan_logs = ScanLog.query.filter_by(student_id=student.id).order_by(ScanLog.scanned_at.desc()).all()
    return render_template('student/profile.html', student=student, scan_logs=scan_logs)

# ==================== PUBLIC ====================
public_bp = Blueprint('public', __name__)

@public_bp.route('/verify/<token>')
def verify(token):
    matric = decrypt_token(token)
    if not matric:
        log_scan(None, 'invalid', request)
        if request.args.get('json'):
            return jsonify({'result': 'invalid', 'student': None, 'photo_url': None})
        return render_template('public/verify.html', student=None, result='invalid',
                               message='This QR code is invalid or has been tampered with.')

    student = Student.query.filter_by(matric_number=matric).first()
    if not student:
        log_scan(None, 'not_found', request)
        if request.args.get('json'):
            return jsonify({'result': 'invalid', 'student': None, 'photo_url': None})
        return render_template('public/verify.html', student=None, result='invalid',
                               message='Student record not found in the system.')

    if student.qr_token != token:
        log_scan(student.id, 'invalid', request)
        if request.args.get('json'):
            return jsonify({'result': 'invalid', 'student': None, 'photo_url': None})
        return render_template('public/verify.html', student=None, result='invalid',
                               message='This QR code has been replaced. Please use the latest card.')

    result = student.card_status
    purpose = request.args.get('purpose', 'general')
    log_scan(student.id, result, request, purpose=purpose)

    if request.args.get('json'):
        photo_url = None
        if student.photo_filename:
            photo_url = url_for('static', filename=f'photos/{student.photo_filename}', _external=False)
        return jsonify({
            'result': result,
            'photo_url': photo_url,
            'student': {
                'full_name': student.full_name,
                'matric_number': student.matric_number,
                'department': student.department,
                'level': student.level,
                'academic_session': student.academic_session,
                'card_status': student.card_status,
            }
        })

    return render_template('public/verify.html', student=student, result=result)

def log_scan(student_id, result, req, purpose='general'):
    try:
        scanned_by = None
        from flask_login import current_user
        if hasattr(current_user, 'id') and current_user.is_authenticated:
            scanned_by = current_user.id
        log = ScanLog(
            student_id=student_id,
            scanned_by=scanned_by,
            purpose=purpose,
            scan_result=result,
            ip_address=req.remote_addr,
            user_agent=req.user_agent.string[:300] if req.user_agent else ''
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass
