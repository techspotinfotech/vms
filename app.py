from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
from database import get_connection
import os
import qrcode
from werkzeug.utils import secure_filename
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

UPLOAD_FOLDER = os.path.join('static','images','visitor_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM admins WHERE email=%s AND password=%s', (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user'] = user['email']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM visitors')
    total_visitors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM visits WHERE status='in'")
    inside = cur.fetchone()[0]
    # fetch some recent rows for table
    cur.close()
    conn.close()
    # pass an empty rows list by default — visitor_list page will fetch actual rows regularly
    return render_template('dashboard.html', total_visitors=total_visitors, inside=inside, rows=[])

@app.route('/add_visitor', methods=['GET','POST'])
@login_required
def add_visitor():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        gender = request.form.get('gender')
        address = request.form.get('address')
        purpose = request.form.get('purpose')
        department = request.form.get('department')
        person_to_meet = request.form.get('person_to_meet')
        photo = request.files.get('photo')
        photo_filename = ''
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            savepath = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(savepath)
            photo_filename = savepath.replace('\\\\','/')
        # Insert visitor
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO visitors (name, phone, email, gender, address, photo) VALUES (%s,%s,%s,%s,%s,%s)',
                    (name, phone, email, gender, address, photo_filename))
        visitor_id = cur.lastrowid
        cur.execute('INSERT INTO visits (visitor_id, purpose, department, person_to_meet, check_in, status) VALUES (%s,%s,%s,%s,NOW(),%s)',
                    (visitor_id, purpose, department, person_to_meet, 'in'))
        visit_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        # generate QR
        qr_path = os.path.join('static','images', f'qr_{visit_id}.png')
        qr = qrcode.make(f'visit:{visit_id}')
        qr.save(qr_path)
        # store qr log
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO qr_logs (visit_id, qr_path) VALUES (%s,%s)', (visit_id, qr_path))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('visitor_list'))
    return render_template('add_visitor.html')

@app.route('/visitor_list')
@login_required
def visitor_list():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT v.id as visitor_id, v.name, v.phone, vi.id as visit_id, vi.purpose, vi.check_in, vi.status FROM visitors v LEFT JOIN visits vi ON v.id = vi.visitor_id ORDER BY vi.check_in DESC')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('visitor_list.html', rows=rows)

@app.route('/view_visitor/<int:visit_id>')
@login_required
def view_visitor(visit_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT vi.*, v.name, v.phone, v.photo FROM visits vi JOIN visitors v ON vi.visitor_id = v.id WHERE vi.id=%s', (visit_id,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    if not data:
        return 'Not found', 404
    return render_template('view_visitor.html', data=data)

@app.route('/static/images/<path:filename>')
def static_images(filename):
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
