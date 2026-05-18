from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import enum

class Role(enum.Enum):
    ADMIN = 'admin'
    STAFF = 'staff'
    STUDENT = 'student'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.STUDENT)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, lazy=True,
                                      foreign_keys='Student.user_id')
    staff_profile = db.relationship('Staff', backref='user', uselist=False, lazy=True,
                                    foreign_keys='Staff.user_id')
    scan_logs_created = db.relationship('ScanLog', backref='scanned_by_user', lazy=True,
                                        foreign_keys='ScanLog.scanned_by')

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matric_number = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    academic_session = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.String(255))
    photo_filename = db.Column(db.String(200))
    qr_token = db.Column(db.String(300), unique=True)
    qr_filename = db.Column(db.String(200))
    card_status = db.Column(db.String(20), default='active')  # active, expired, suspended
    card_expiry = db.Column(db.Date)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    scan_logs = db.relationship('ScanLog', backref='student', lazy=True,
                                foreign_keys='ScanLog.student_id')

    def __repr__(self):
        return f'<Student {self.matric_number}>'

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    staff_id = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Staff {self.staff_id}>'

class ScanLog(db.Model):
    __tablename__ = 'scan_logs'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    scanned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    location = db.Column(db.String(100))
    purpose = db.Column(db.String(50))  # exam, event, gate, general
    scan_result = db.Column(db.String(20))  # valid, invalid, expired, suspended
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(300))
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScanLog {self.id}>'


class School(db.Model):
    __tablename__ = 'schools'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(150), unique=True, nullable=False)
    short_name   = db.Column(db.String(50))
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    departments  = db.relationship('Department', backref='school', lazy=True,
                                   cascade='all, delete-orphan')

    def __repr__(self):
        return f'<School {self.name}>'


class Department(db.Model):
    __tablename__ = 'departments'
    id              = db.Column(db.Integer, primary_key=True)
    school_id       = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name            = db.Column(db.String(150), nullable=False)
    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    specializations = db.relationship('Specialization', backref='department', lazy=True,
                                      cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Department {self.name}>'


class Specialization(db.Model):
    __tablename__ = 'specializations'
    id            = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    name          = db.Column(db.String(150), nullable=False)
    levels        = db.Column(db.String(50), default='HND 1,HND 2')  # CSV of applicable levels
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Specialization {self.name}>'
