# app/routes.py
from flask import render_template, jsonify, request, current_app
import json
import os
import requests

def load_json_data(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def register_routes(app):
    """Đăng ký tất cả routes với app instance"""
    
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