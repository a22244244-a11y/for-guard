import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///happycall.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    TEST_ADMIN_USERNAME = os.environ.get('TEST_ADMIN_USERNAME', '1')
    TEST_ADMIN_PASSWORD = os.environ.get('TEST_ADMIN_PASSWORD', '1')
    TEST_FREELANCER_USERNAME = os.environ.get('TEST_FREELANCER_USERNAME', '2')
    TEST_FREELANCER_PASSWORD = os.environ.get('TEST_FREELANCER_PASSWORD', '2')

    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
