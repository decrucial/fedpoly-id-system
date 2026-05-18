from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.models import User, Role
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)

def is_account_locked(user):
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    return True, ""

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.STAFF:
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    return render_template('auth/landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Contact the administrator.', 'danger')
            return render_template('auth/login.html')

        if is_account_locked(user):
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            flash(f'Account locked due to too many failed attempts. Try again in {remaining} minutes.', 'danger')
            return render_template('auth/login.html')

        if bcrypt.check_password_hash(user.password_hash, password):
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.session.commit()

            login_user(user, remember=remember)

            if user.must_change_password:
                flash('Please change your default password before continuing.', 'warning')
                return redirect(url_for('auth.change_password'))

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif user.role == Role.STAFF:
                return redirect(url_for('staff.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                flash('Too many failed attempts. Account locked for 30 minutes.', 'danger')
            else:
                remaining = 5 - user.failed_login_attempts
                flash(f'Invalid password. {remaining} attempts remaining.', 'danger')
            db.session.commit()

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')

        valid, msg = validate_password_strength(new_password)
        if not valid:
            flash(msg, 'danger')
            return render_template('auth/change_password.html')

        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        current_user.must_change_password = False
        db.session.commit()
        flash('Password changed successfully!', 'success')

        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.STAFF:
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('auth/change_password.html')
