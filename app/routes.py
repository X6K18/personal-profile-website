# app/routes.py
from flask import render_template, jsonify, request, current_app, session, redirect, url_for, flash
import json
import os
import requests
import hashlib
from datetime import datetime
from functools import wraps

# ==========================================
# CÁC HÀM TRỢ GIÚP (HELPER FUNCTIONS)
# ==========================================

def load_json_data(filename):
    """Đọc dữ liệu từ file JSON một cách an toàn"""
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def hash_password(password):
    """Mã hóa mật khẩu bằng SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Đọc danh sách users từ JSON"""
    return load_json_data('users.json')

def save_users(users_data):
    """Lưu danh sách users vào JSON"""
    # Đảm bảo thư mục 'data' tồn tại
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, 'users.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)

def get_next_user_id(users_data):
    """Lấy ID tiếp theo cho user mới"""
    users_list = users_data.get('users', [])
    if not users_list:
        return 1
    return max(user['id'] for user in users_list) + 1

def login_required(f):
    """Decorator để bảo vệ các route yêu cầu đăng nhập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# ĐĂNG KÝ TẤT CẢ ROUTES VÀO APP
# ==========================================

def register_routes(app):
    """Đăng ký tất cả các routes của ứng dụng với app instance"""
    
    @app.route('/')
    def index():
        profile = load_json_data('profile.json')
        return render_template('index.html', profile=profile)

    @app.route('/about')
    def about():
        profile = load_json_data('profile.json')
        return render_template('about.html', profile=profile)

    @app.route('/skills')
    def skills():
        skills_data = load_json_data('skills.json')
        return render_template('skills.html', skills=skills_data)

    @app.route('/projects')
    def projects():
        projects_data = load_json_data('projects.json')
        github_username = app.config.get('GITHUB_USERNAME', 'your-github-username')
        
        github_repos = []
        if github_username and github_username != 'your-github-username':
            try:
                response = requests.get(f'https://api.github.com/users/{github_username}/repos', 
                                       params={'sort': 'updated', 'per_page': 6}, 
                                       timeout=10)
                if response.status_code == 200:
                    github_repos = response.json()
            except Exception as e:
                print(f"Error fetching GitHub repos: {e}")
        
        return render_template('projects.html', projects=projects_data, 
                               github_repos=github_repos, github_username=github_username)

    @app.route('/contact')
    def contact():
        contacts = load_json_data('contacts.json')
        return render_template('contact.html', contacts=contacts)

    @app.route('/api/github-repos')
    def api_github_repos():
        github_username = app.config.get('GITHUB_USERNAME', 'your-github-username')
        if github_username and github_username != 'your-github-username':
            try:
                response = requests.get(f'https://api.github.com/users/{github_username}/repos',
                                       params={'sort': 'updated', 'per_page': 10},
                                       timeout=10)
                return jsonify(response.json())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return jsonify([])

    # --- HỆ THỐNG ĐĂNG NHẬP / ĐĂNG KÝ (ĐÃ FIX SỬ DỤNG @app.route) ---

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if session.get('user_id'):
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            users_data = load_users()
            user = None
            
            # Tìm user theo username hoặc email
            for u in users_data.get('users', []):
                if u['username'] == username or u['email'] == username:
                    user = u
                    break
            
            # Kiểm tra mật khẩu
            if user and user['password'] == hash_password(password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['fullname'] = user.get('fullname', user['username'])
                flash(f'Welcome back, {session["fullname"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username/email or password!', 'error')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if session.get('user_id'):
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            fullname = request.form.get('fullname', '').strip()
            
            errors = []
            
            # 1. Validate định dạng cơ bản
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters.')
            if not email or '@' not in email:
                errors.append('Invalid email address.')
            if not password or len(password) < 6:
                errors.append('Password must be at least 6 characters.')
            if password != confirm_password:
                errors.append('Passwords do not match.')
            
            # 2. Kiểm tra trùng lặp (Chỉ kiểm tra nếu các bước trên hợp lệ)
            if not errors:
                users_data = load_users()
                for u in users_data.get('users', []):
                    if u['username'].lower() == username.lower():
                        errors.append('Username already exists.')
                        break
                    if u['email'].lower() == email.lower():
                        errors.append('Email already registered.')
                        break
            
            # 3. Xử lý kết quả kiểm tra
            if errors:
                for error in errors:
                    flash(error, 'error')
            else:
                # Tạo user mới sau khi chắc chắn không có lỗi nào
                new_user = {
                    'id': get_next_user_id(users_data),
                    'username': username,
                    'email': email,
                    'password': hash_password(password),
                    'fullname': fullname or username,
                    'created_at': datetime.now().isoformat()
                }
                users_data.setdefault('users', []).append(new_user)
                save_users(users_data)
                
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
        
        return render_template('register.html')

    # --- API ENDPOINTS CHO CLIENT-SIDE JS ---

    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Please fill in all fields'}), 400

        users_data = load_users()
        user = None

        for u in users_data.get('users', []):
            if u['username'] == username or u['email'] == username:
                user = u
                break

        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['fullname'] = user.get('fullname', user['username'])
            return jsonify({'success': True, 'message': f'Welcome back, {session["fullname"]}!', 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Invalid username/email or password!'}), 401

    @app.route('/api/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        fullname = data.get('fullname', '').strip()

        errors = []

        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Invalid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if not errors:
            users_data = load_users()
            for u in users_data.get('users', []):
                if u['username'].lower() == username.lower():
                    errors.append('Username already exists.')
                    break
                if u['email'].lower() == email.lower():
                    errors.append('Email already registered.')
                    break

        if errors:
            return jsonify({'success': False, 'message': errors[0]}), 400
        else:
            new_user = {
                'id': get_next_user_id(users_data),
                'username': username,
                'email': email,
                'password': hash_password(password),
                'fullname': fullname or username,
                'created_at': datetime.now().isoformat()
            }
            users_data.setdefault('users', []).append(new_user)
            save_users(users_data)
            return jsonify({'success': True, 'message': 'Registration successful! Please login.', 'redirect': url_for('login')})

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/profile')
    @login_required
    def user_profile():
        users_data = load_users()
        user = None
        for u in users_data.get('users', []):
            if u['id'] == session.get('user_id'):
                user = u
                break
        return render_template('profile.html', user=user)