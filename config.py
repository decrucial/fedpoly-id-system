import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Auto-create all required directories on startup (Windows & Linux safe)
_INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
_PHOTOS_DIR   = os.path.join(BASE_DIR, 'app', 'static', 'photos')
_QR_DIR       = os.path.join(BASE_DIR, 'app', 'static', 'qrcodes')
_CARD_DIR     = os.path.join(BASE_DIR, 'app', 'static', 'idcards')

for _d in [_INSTANCE_DIR, _PHOTOS_DIR, _QR_DIR, _CARD_DIR]:
    os.makedirs(_d, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fedpoly-nasarawa-qr-id-system-2024-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(_INSTANCE_DIR, 'fedpoly.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = _PHOTOS_DIR
    QR_FOLDER     = _QR_DIR
    IDCARD_FOLDER = _CARD_DIR
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE   = False   # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # App info
    SCHOOL_NAME   = "The Federal Polytechnic Nasarawa"
    SCHOOL_SHORT  = "FedPolyNasarawa"
    SCHOOL_DEPT   = "Department of Computer Science"
    SCHOOL_SCHOOL = "School of Information Technology"
    CURRENT_SESSION = "2024/2025"
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'

    # Encryption key for QR tokens
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'fedpoly-nasarawa-enc-key-2024-xyz'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
