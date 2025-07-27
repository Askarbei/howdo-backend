from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
import tempfile
from werkzeug.security import generate_password_hash, check_password_hash
from document_generator import DocumentGenerator

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
                document_type TEXT DEFAULT 'sok',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    document_type = data.get('documentType', 'sok')  # По умолчанию СОК
    
    # Определяем название документа на основе типа
    type_names = {
        'sok': 'СОК',
        'instruction': 'Рабочая инструкция', 
        'procedure': 'Стандарт процедуры'
    }
    
    company_name = answers.get('q1', 'Компания')
    process_name = answers.get('q3', 'Процесс')
    title = f"{type_names.get(document_type, 'Документ')} - {process_name} ({company_name})"

    if not user_id or not answers:
        return jsonify({"error": "User ID and answers are required"}), 400

    content = json.dumps(answers, ensure_ascii=False)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO documents (user_id, title, content, document_type) VALUES (?, ?, ?, ?)",
            (user_id, title, content, document_type)
        )
        db.commit()
        document_id = cursor.lastrowid
        return jsonify({
            "message": "Document saved successfully", 
            "document_id": document_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<int:user_id>', methods=['GET'])
def get_documents(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, title, document_type, created_at FROM documents WHERE user_id = ? ORDER BY created_at DESC", 
            (user_id,)
        )
        documents = cursor.fetchall()
        return jsonify([dict(doc) for doc in documents]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/document/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Получить полную информацию о документе"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE id = ?", 
            (document_id,)
        )
        document = cursor.fetchone()
        
        if not document:
            return jsonify({"error": "Document not found"}), 404
            
        return jsonify({
            "id": document['id'],
            "title": document['title'],
            "content": json.loads(document['content']),
            "document_type": document['document_type'],
            "created_at": document['created_at']
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/<int:document_id>', methods=['GET'])
def export_document(document_id):
    """Экспорт документа в PDF"""
    try:
        # Получаем документ из базы данных
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE id = ?", 
            (document_id,)
        )
        document = cursor.fetchone()
        
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        # Парсим содержимое документа
        content = json.loads(document['content'])
        document_type = document['document_type']
        title = document['title']
        
        # Создаем генератор документов
        generator = DocumentGenerator()
        
        # Создаем временный файл для PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        try:
            # Генерируем PDF с помощью WeasyPrint (более надежно чем pdfkit)
            html_content = generator.generate_html(document_type, content)
            
            # Используем WeasyPrint для генерации PDF
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(pdf_path)
            
            # Формируем имя файла для скачивания
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.pdf"
            
            # Отправляем файл пользователю
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            # Если PDF не удался, отправляем HTML
            html_content = generator.generate_html(document_type, content)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                tmp_file.write(html_content)
                html_path = tmp_file.name
            
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.html"
            
            return send_file(
                html_path,
                as_attachment=True,
                download_name=filename,
                mimetype='text/html'
            )
        
        finally:
            # Очищаем временные файлы
            try:
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
            except:
                pass
                
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

@app.route('/api/export/<int:document_id>/preview', methods=['GET'])
def preview_document(document_id):
    """Предварительный просмотр документа в HTML"""
    try:
        # Получаем документ из базы данных
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE id = ?", 
            (document_id,)
        )
        document = cursor.fetchone()
        
        if not document:
            return jsonify({"error": "Document not found"}), 404
        
        # Парсим содержимое документа
        content = json.loads(document['content'])
        document_type = document['document_type']
        
        # Создаем генератор документов
        generator = DocumentGenerator()
        
        # Генерируем HTML
        html_content = generator.generate_html(document_type, content)
        
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        return jsonify({"error": f"Preview failed: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
