from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

DATABASE = 'howdo.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                company TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()

@app.route('/')
def home():
    return "Hello from HowDo Backend!"

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    company = data.get('company')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    hashed_password = generate_password_hash(password)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, password, name, company) VALUES (?, ?, ?, ?)",
            (email, hashed_password, name, company)
        )
        db.commit()
        user_id = cursor.lastrowid
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        user_data = {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "company": user['company']
        }
        return jsonify({"message": "Login successful", "user": user_data}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/wizard', methods=['POST'])
def save_wizard_data():
    data = request.get_json()
    user_id = data.get('userId')
    answers = data.get('answers')
    title = f"Документ от {answers.get('q1', 'Пользователя')}"

    if not user_id or not answers:
        return jsonify({"error": "User ID and answers are required"}), 400

    content = json.dumps(answers, ensure_ascii=False)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO documents (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content)
        )
        db.commit()
        return jsonify({"message": "Document saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<int:user_id>', methods=['GET'])
def get_documents(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, title FROM documents WHERE user_id = ?", (user_id,))
        documents = cursor.fetchall()
        return jsonify([dict(doc) for doc in documents]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
