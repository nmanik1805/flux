from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'advert-ai-secret-2025')

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://flux_user:flux_user@flux-dev.ha40zia.mongodb.net/?appName=flux-dev')
client = MongoClient(MONGO_URI)
db = client['ai_advert_db']
requests_col = db['customer_requests']
users_col = db['admin_users']
settings_col = db['settings']


# ── Timezone ──────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

def format_ist(dt):
    if dt is None:
        return '—'
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
    else:
        dt = dt.astimezone(IST)
    return dt.strftime('%d %b %Y, %I:%M %p IST')
# ──────────────────────────────────────────────────────────

# Initialize default admin user if not exists
def init_admin():
    if users_col.count_documents({}) == 0:
        users_col.insert_one({
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'role': 'super_admin',
            'created_at': now_ist()
        })

init_admin()

# ─── PUBLIC ROUTES ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-request', methods=['POST'])
def submit_request():
    data = request.get_json()
    
    # Validate phone number
    phone = data.get('phone', '').strip()
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({'success': False, 'message': 'Phone number must be exactly 10 digits.'}), 400
    
    doc = {
        'requestor_name': data.get('requestor_name', '').strip(),
        'company_name': data.get('company_name', '').strip(),
        'email': data.get('email', '').strip(),
        'phone': phone,
        'how_contacted': data.get('how_contacted', '').strip(),
        'requirement': data.get('requirement', '').strip(),
        'status': 'Customer Contacted',
        'assignee': None,
        'created_at': now_ist(),
        'updated_at': now_ist()
    }
    
    requests_col.insert_one(doc)
    return jsonify({'success': True, 'message': 'Request submitted successfully!'})

# ─── ADMIN AUTH ROUTES ────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_col.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_role'] = user.get('role', 'admin')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid username or password.')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── ADMIN DASHBOARD ──────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', 
                           username=session.get('admin_username'),
                           role=session.get('admin_role'))

# ─── ADMIN API: PROJECTS ──────────────────────────────────────────────────────

@app.route('/admin/api/projects')
@admin_required
def api_projects():
    tab = request.args.get('tab', 'active')
    
    if tab == 'active':
        docs = list(requests_col.find({'status': {'$ne': 'completed'}}))
    else:
        docs = list(requests_col.find())
    
    for d in docs:
        d['_id'] = str(d['_id'])
        if d.get('created_at'):
           d['created_at'] = format_ist(d.get('created_at'))
        if d.get('updated_at'):
            d['updated_at'] = format_ist(d.get('updated_at'))
    
    return jsonify(docs)

@app.route('/admin/api/projects/<project_id>', methods=['PUT'])
@admin_required
def api_update_project(project_id):
    data = request.get_json()
    update_fields = {}
    
    if 'status' in data:
        update_fields['status'] = data['status']
    if 'assignee' in data:
        update_fields['assignee'] = data['assignee'] if data['assignee'] else None
    
    update_fields['updated_at'] = now_ist()
    
    requests_col.update_one(
        {'_id': ObjectId(project_id)},
        {'$set': update_fields}
    )
    return jsonify({'success': True})

@app.route('/admin/api/projects/<project_id>', methods=['DELETE'])
@admin_required
def api_delete_project(project_id):
    requests_col.delete_one({'_id': ObjectId(project_id)})
    return jsonify({'success': True})

@app.route('/admin/api/projects/<project_id>', methods=['GET'])
@admin_required
def api_get_project(project_id):
    doc = requests_col.find_one({'_id': ObjectId(project_id)})
    if doc:
        doc['_id'] = str(doc['_id'])
        if doc.get('created_at'):
           doc['created_at'] = format_ist(doc.get('created_at'))
        if doc.get('updated_at'):
            doc['updated_at'] = format_ist(doc.get('updated_at'))
        return jsonify(doc)
    return jsonify({'error': 'Not found'}), 404

# ─── ADMIN API: USER MANAGEMENT ───────────────────────────────────────────────

@app.route('/admin/api/users')
@admin_required
def api_users():
    users = list(users_col.find({}, {'password': 0}))
    for u in users:
        u['_id'] = str(u['_id'])
        if u.get('created_at'):
            u['created_at'] = u['created_at'].strftime('%d %b %Y')
    return jsonify(users)

@app.route('/admin/api/users', methods=['POST'])
@admin_required
def api_create_user():
    if session.get('admin_role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'admin')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required.'}), 400
    
    if users_col.find_one({'username': username}):
        return jsonify({'success': False, 'message': 'Username already exists.'}), 400
    
    users_col.insert_one({
        'username': username,
        'password': generate_password_hash(password),
        'role': role,
        'created_at': now_ist()
    })
    return jsonify({'success': True})

@app.route('/admin/api/users/<user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    if session.get('admin_role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Prevent deleting own account
    user = users_col.find_one({'_id': ObjectId(user_id)})
    if user and user['username'] == session.get('admin_username'):
        return jsonify({'success': False, 'message': 'Cannot delete your own account.'}), 400
    
    users_col.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'success': True})

@app.route('/admin/api/users/<user_id>/reset-password', methods=['PUT'])
@admin_required
def api_reset_password(user_id):
    if session.get('admin_role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_password = data.get('password', '').strip()
    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400
    
    users_col.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'password': generate_password_hash(new_password)}}
    )
    return jsonify({'success': True})

# ─── ADMIN API: STATS ─────────────────────────────────────────────────────────

@app.route('/admin/api/stats')
@admin_required
def api_stats():
    total = requests_col.count_documents({})
    new_count = requests_col.count_documents({'status': 'Customer Contacted'})
    active_count = requests_col.count_documents({'status': {'$ne': 'completed'}})
    completed = requests_col.count_documents({'status': 'completed'})
    return jsonify({
        'total': total,
        'new': new_count,
        'active': active_count,
        'completed': completed
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
