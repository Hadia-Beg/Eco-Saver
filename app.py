from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'supersecretkey'
bcrypt = Bcrypt(app)

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_type TEXT,
            brand TEXT,
            description TEXT,
            image BLOB
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            message TEXT
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculator_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            steel REAL,
            rubber REAL,
            plastic REAL,
            cardboard REAL,
            paper REAL,
            estimated_value REAL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            phone TEXT
        )''')
        
        db.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        product_type = request.form['product_type']
        brand = request.form['brand']
        description = request.form['description']
        image = request.files['image'].read() if 'image' in request.files else None

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (product_type, brand, description, image)
                VALUES (?, ?, ?, ?)
            ''', (product_type, brand, description, image))
            db.commit()
            flash('Product added successfully!')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            db.rollback()
        return redirect(url_for('sell'))
    
    return render_template('sell.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO contacts (name, email, phone, message)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, message))
            db.commit()
            flash('Message sent successfully!')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            db.rollback()
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        steel = float(request.form['steel']) if request.form['steel'] else 0
        rubber = float(request.form['rubber']) if request.form['rubber'] else 0
        plastic = float(request.form['plastic']) if request.form['plastic'] else 0
        cardboard = float(request.form['cardboard']) if request.form['cardboard'] else 0
        paper = float(request.form['paper']) if request.form['paper'] else 0
        
        prices = {
            'steel': 142.5,
            'rubber': 114,
            'plastic': 85.5,
            'cardboard': 28.5,
            'paper': 42.75
        }

        estimated_value = (steel * prices['steel'] +
                           rubber * prices['rubber'] +
                           plastic * prices['plastic'] +
                           cardboard * prices['cardboard'] +
                           paper * prices['paper'])

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO calculator_results (steel, rubber, plastic, cardboard, paper, estimated_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (steel, rubber, plastic, cardboard, paper, estimated_value))
        db.commit()

        return render_template('calculator.html', estimated_value=estimated_value)
    return render_template('calculator.html')

@app.route('/productfull')
def productfull():
    return render_template('productfull.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message')
    
    if message:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO chat_messages (message)
            VALUES (?)
        ''', (message,))
        db.commit()
        return jsonify({'status': 'success'}), 201
    return jsonify({'status': 'error', 'message': 'No message provided'}), 400

@app.route('/get_messages', methods=['GET'])
def get_messages():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM chat_messages ORDER BY timestamp ASC')
    messages = cursor.fetchall()
    message_list = [{'message': row['message'], 'timestamp': row['timestamp']} for row in messages]
    return jsonify(message_list)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, phone)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed_password, phone))
            db.commit()
            flash('Signup successful! You can now log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            db.rollback()
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and password.')

    return render_template('login.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
