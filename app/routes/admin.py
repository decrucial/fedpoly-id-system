from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db, bcrypt
from app.models.models import User, Student, Staff, ScanLog, Role
from app.utils.qr_utils import generate_token, generate_qr_code, generate_id_card_image, generate_id_card_pdf
from app.utils.helpers import allowed_file, save_photo, get_dashboard_stats
from app.utils.report_utils import generate_students_report, generate_scan_logs_report, generate_single_student_report
from datetime import datetime, date
import os, io

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template('admin/dashboard.html', **stats)

# ---- STUDENT MANAGEMENT ----

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    level = request.args.get('level', '')
    status = request.args.get('status', '')

    query = Student.query
    if search:
        query = query.filter(
            (Student.full_name.ilike(f'%{search}%')) |
            (Student.matric_number.ilike(f'%{search}%'))
        )
    if department:
        query = query.filter_by(department=department)
    if level:
        query = query.filter_by(level=level)
    if status:
        query = query.filter_by(card_status=status)

    students = query.order_by(Student.registered_at.desc()).all()
    departments = db.session.query(Student.department).distinct().all()
    return render_template('admin/students.html', students=students,
                           departments=[d[0] for d in departments],
                           search=search, department=department, level=level, status=status)

@admin_bp.route('/students/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_student():
    if request.method == 'POST':
        matric = request.form.get('matric_number', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        # department hidden field already has full name e.g.
        # 'Computer Science' or 'Computer Science (Networking & Cloud Computing)'
        department = request.form.get('department', '').strip()
        school = request.form.get('school', '').strip()
        level = request.form.get('level', '').strip()
        session_val = request.form.get('academic_session', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        address = request.form.get('address', '').strip()
        expiry_str = request.form.get('card_expiry', '').strip()

        # Validations
        if Student.query.filter_by(matric_number=matric).first():
            flash(f'Matric number {matric} is already registered.', 'danger')
            return render_template('admin/register_student.html')

        if not all([matric, full_name, department, level, session_val]):
            flash('Please fill all required fields.', 'danger')
            return render_template('admin/register_student.html')

        # Create user account
        username = matric.lower().replace('/', '')
        email = f"{username}@student.fedpolynas.edu.ng"
        password_hash = bcrypt.generate_password_hash('Student@2024').decode('utf-8')

        user = User(username=username, email=email, password_hash=password_hash,
                    role=Role.STUDENT, must_change_password=True)
        db.session.add(user)
        db.session.flush()

        # Handle photo
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename and allowed_file(photo.filename):
                photo_filename = save_photo(photo, matric)

        # Parse dates
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None

        # Generate QR token
        token = generate_token(matric)

        student = Student(
            user_id=user.id,
            matric_number=matric,
            full_name=full_name,
            department=department,
            school=school or current_app.config['SCHOOL_SCHOOL'],
            level=level,
            academic_session=session_val,
            gender=gender,
            phone=phone,
            date_of_birth=dob,
            address=address,
            photo_filename=photo_filename,
            qr_token=token,
            card_status='active',
            card_expiry=expiry,
            registered_by=current_user.id
        )
        db.session.add(student)
        db.session.flush()

        # Generate QR code image
        qr_filename = generate_qr_code(token, matric)
        student.qr_filename = qr_filename
        db.session.commit()

        flash(f'Student {full_name} registered successfully! Login: {username} / Student@2024', 'success')
        return redirect(url_for('admin.view_student', student_id=student.id))

    from app.models.models import School
    schools = School.query.filter_by(is_active=True).order_by(School.name).all()
    return render_template('admin/register_student.html',
                           current_session=current_app.config['CURRENT_SESSION'],
                           schools=schools)

@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    scan_logs = ScanLog.query.filter_by(student_id=student.id).order_by(ScanLog.scanned_at.desc()).limit(20).all()
    return render_template('admin/view_student.html', student=student, scan_logs=scan_logs)

@admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.full_name = request.form.get('full_name', student.full_name).strip()
        student.department = request.form.get('department', student.department).strip()
        student.school = request.form.get('school', student.school).strip()
        student.level = request.form.get('level', student.level).strip()
        student.academic_session = request.form.get('academic_session', student.academic_session).strip()
        student.gender = request.form.get('gender', student.gender)
        student.phone = request.form.get('phone', student.phone)
        student.address = request.form.get('address', student.address)
        expiry_str = request.form.get('card_expiry', '')
        if expiry_str:
            student.card_expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date()

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename and allowed_file(photo.filename):
                student.photo_filename = save_photo(photo, student.matric_number)
                # Regenerate ID card
                generate_id_card_image(student)

        db.session.commit()
        flash('Student information updated successfully.', 'success')
        return redirect(url_for('admin.view_student', student_id=student.id))

    return render_template('admin/edit_student.html', student=student)

@admin_bp.route('/students/<int:student_id>/toggle-status')
@login_required
@admin_required
def toggle_student_status(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    if student.card_status == 'active':
        student.card_status = 'suspended'
        if user: user.is_active = False
        flash(f'{student.full_name} has been suspended.', 'warning')
    else:
        student.card_status = 'active'
        if user: user.is_active = True
        flash(f'{student.full_name} has been reactivated.', 'success')
    db.session.commit()
    return redirect(url_for('admin.view_student', student_id=student.id))

@admin_bp.route('/students/<int:student_id>/regenerate-qr')
@login_required
@admin_required
def regenerate_qr(student_id):
    student = Student.query.get_or_404(student_id)
    token = generate_token(student.matric_number)
    student.qr_token = token
    qr_filename = generate_qr_code(token, student.matric_number)
    student.qr_filename = qr_filename
    db.session.commit()
    flash('QR code regenerated successfully.', 'success')
    return redirect(url_for('admin.view_student', student_id=student.id))

# ---- ID CARD DOWNLOAD ----

@admin_bp.route('/students/<int:student_id>/download-card/<fmt>')
@login_required
@admin_required
def download_card(student_id, fmt):
    student = Student.query.get_or_404(student_id)
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

# ---- STAFF MANAGEMENT ----

@admin_bp.route('/staff')
@login_required
@admin_required
def staff_list():
    staff = Staff.query.order_by(Staff.created_at.desc()).all()
    return render_template('admin/staff.html', staff=staff)

@admin_bp.route('/staff/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_staff():
    if request.method == 'POST':
        staff_id = request.form.get('staff_id', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()

        if Staff.query.filter_by(staff_id=staff_id).first():
            flash(f'Staff ID {staff_id} already exists.', 'danger')
            return render_template('admin/register_staff.html')

        username = staff_id.lower().replace('/', '')
        password_hash = bcrypt.generate_password_hash('Staff@FedPoly2024').decode('utf-8')
        user = User(username=username, email=email, password_hash=password_hash,
                    role=Role.STAFF, must_change_password=True)
        db.session.add(user)
        db.session.flush()

        staff = Staff(user_id=user.id, staff_id=staff_id, full_name=full_name,
                      department=department, designation=designation, phone=phone)
        db.session.add(staff)
        db.session.commit()
        flash(f'Staff {full_name} registered. Login: {username} / Staff@FedPoly2024', 'success')
        return redirect(url_for('admin.staff_list'))

    return render_template('admin/register_staff.html')

@admin_bp.route('/staff/<int:staff_id>/toggle')
@login_required
@admin_required
def toggle_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    user = User.query.get(staff.user_id)
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'{staff.full_name} has been {status}.', 'info')
    return redirect(url_for('admin.staff_list'))

# ---- SCAN LOGS ----

@admin_bp.route('/scan-logs')
@login_required
@admin_required
def scan_logs():
    page = request.args.get('page', 1, type=int)
    purpose = request.args.get('purpose', '')
    result = request.args.get('result', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = ScanLog.query
    if purpose:
        query = query.filter_by(purpose=purpose)
    if result:
        query = query.filter_by(scan_result=result)
    if date_from:
        query = query.filter(ScanLog.scanned_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(ScanLog.scanned_at <= datetime.strptime(date_to, '%Y-%m-%d'))

    logs = query.order_by(ScanLog.scanned_at.desc()).paginate(page=page, per_page=30)
    return render_template('admin/scan_logs.html', logs=logs, purpose=purpose,
                           result=result, date_from=date_from, date_to=date_to)

# ---- REPORTS ----

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    stats = get_dashboard_stats()
    return render_template('admin/reports.html', **stats)

@admin_bp.route('/reports/students/pdf')
@login_required
@admin_required
def report_students_pdf():
    department = request.args.get('department', '')
    level = request.args.get('level', '')
    status = request.args.get('status', '')

    query = Student.query
    filters = {}
    if department:
        query = query.filter_by(department=department)
        filters['Department'] = department
    if level:
        query = query.filter_by(level=level)
        filters['Level'] = level
    if status:
        query = query.filter_by(card_status=status)
        filters['Status'] = status

    students = query.order_by(Student.full_name).all()
    buf = generate_students_report(students, current_app._get_current_object(), filters)
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name='Students_Report.pdf')

@admin_bp.route('/reports/scan-logs/pdf')
@login_required
@admin_required
def report_scan_logs_pdf():
    logs = ScanLog.query.order_by(ScanLog.scanned_at.desc()).all()
    buf = generate_scan_logs_report(logs, current_app._get_current_object())
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name='Scan_Logs_Report.pdf')

@admin_bp.route('/reports/student/<int:student_id>/pdf')
@login_required
@admin_required
def report_single_student_pdf(student_id):
    student = Student.query.get_or_404(student_id)
    logs = ScanLog.query.filter_by(student_id=student_id).order_by(ScanLog.scanned_at.desc()).all()
    buf = generate_single_student_report(student, logs, current_app._get_current_object())
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name=f'Student_{student.matric_number.replace("/","_")}_Report.pdf')

# ======================================================================
# DEPARTMENT / SCHOOL / SPECIALIZATION MANAGEMENT
# ======================================================================

from app.models.models import School, Department, Specialization

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    schools = School.query.order_by(School.name).all()
    return render_template('admin/departments.html', schools=schools)

# ── Schools ────────────────────────────────────────────────────────────
@admin_bp.route('/departments/school/add', methods=['POST'])
@login_required
@admin_required
def add_school():
    name       = request.form.get('name', '').strip()
    short_name = request.form.get('short_name', '').strip()
    if not name:
        flash('School name is required.', 'danger')
    elif School.query.filter_by(name=name).first():
        flash(f'School "{name}" already exists.', 'danger')
    else:
        db.session.add(School(name=name, short_name=short_name))
        db.session.commit()
        flash(f'School "{name}" added successfully.', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/school/<int:school_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_school(school_id):
    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    flash(f'School "{school.name}" deleted.', 'warning')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/school/<int:school_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_school(school_id):
    school = School.query.get_or_404(school_id)
    school.is_active = not school.is_active
    db.session.commit()
    status = 'activated' if school.is_active else 'deactivated'
    flash(f'School "{school.name}" {status}.', 'info')
    return redirect(url_for('admin.departments'))

# ── Departments ────────────────────────────────────────────────────────
@admin_bp.route('/departments/dept/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    name      = request.form.get('name', '').strip()
    school_id = request.form.get('school_id', type=int)
    if not name or not school_id:
        flash('Department name and school are required.', 'danger')
    else:
        db.session.add(Department(school_id=school_id, name=name))
        db.session.commit()
        flash(f'Department "{name}" added successfully.', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/dept/<int:dept_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash(f'Department "{dept.name}" deleted.', 'warning')
    return redirect(url_for('admin.departments'))

# ── Specializations ────────────────────────────────────────────────────
@admin_bp.route('/departments/spec/add', methods=['POST'])
@login_required
@admin_required
def add_specialization():
    name      = request.form.get('name', '').strip()
    dept_id   = request.form.get('dept_id', type=int)
    levels    = request.form.get('levels', '').strip()
    if not name or not dept_id:
        flash('Specialization name and department are required.', 'danger')
    else:
        db.session.add(Specialization(department_id=dept_id, name=name, levels=levels))
        db.session.commit()
        flash(f'Specialization "{name}" added successfully.', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/departments/spec/<int:spec_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_specialization(spec_id):
    spec = Specialization.query.get_or_404(spec_id)
    db.session.delete(spec)
    db.session.commit()
    flash(f'Specialization "{spec.name}" deleted.', 'warning')
    return redirect(url_for('admin.departments'))

# ── JSON APIs for registration form ───────────────────────────────────
@admin_bp.route('/api/schools')
@login_required
def api_schools():
    schools = School.query.filter_by(is_active=True).order_by(School.name).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in schools])

@admin_bp.route('/api/departments/<int:school_id>')
@login_required
def api_departments(school_id):
    depts = Department.query.filter_by(school_id=school_id, is_active=True).order_by(Department.name).all()
    return jsonify([{'id': d.id, 'name': d.name} for d in depts])

@admin_bp.route('/api/specializations/<int:dept_id>')
@login_required
def api_specializations(dept_id):
    specs = Specialization.query.filter_by(department_id=dept_id, is_active=True).order_by(Specialization.name).all()
    return jsonify([{'id': s.id, 'name': s.name, 'levels': s.levels} for s in specs])
