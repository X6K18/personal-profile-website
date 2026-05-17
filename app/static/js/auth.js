// ============================================
// AUTH.JS - Authentication functionality
// ============================================

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button class="alert-close">&times;</button>
    `;
    
    container.appendChild(alert);
    
    setTimeout(() => {
        if (alert && alert.remove) alert.remove();
    }, 5000);
    
    alert.querySelector('.alert-close').addEventListener('click', () => {
        alert.remove();
    });
}

/**
 * Handle login
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showAlert('Please fill in all fields', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Signing in...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            showAlert(data.message || 'Invalid credentials', 'error');
        }
    } catch (error) {
        showAlert('Network error. Please try again.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Handle register
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const formData = {
        username: document.getElementById('username').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        confirm_password: document.getElementById('confirm_password').value,
        fullname: document.getElementById('fullname').value
    };
    
    if (formData.password !== formData.confirm_password) {
        showAlert('Passwords do not match', 'error');
        return;
    }
    
    if (formData.password.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Creating account...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1500);
        } else {
            showAlert(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        showAlert('Network error. Please try again.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Initialize forms
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});