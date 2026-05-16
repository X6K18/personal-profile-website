# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'your-github-username')
    
    # Cấu hình thêm
    DEBUG = True
    TESTING = False