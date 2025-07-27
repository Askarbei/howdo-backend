from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
import uuid
import sqlite3
from datetime import datetime
from document_generator import DocumentGenerator

app = Flask(__name__)
CORS(app)

# Инициализация генератора документов
generator = DocumentGenerator()

# Инициализация SQLite базы данных
def init_database():
    """Создание таблиц в SQLite базе данных"""
    conn = sqlite3.connect('howdo.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Таблица документов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            answers TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Инициализация базы данных при запуске
init_database()

def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect('howdo.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/debug', methods=['GET'])
def debug_data():
    """DEBUG: Просмотр всех данных в базе"""
    try:
        conn = get_db_connection()
        
        # Получение всех пользователей
        users = conn.execute('SELECT * FROM users').fetchall()
        users_list = [dict(u) for u in users]
        
        # Получение всех документов
        documents = conn.execute('SELECT * FROM documents').fetchall()
        documents_list = [dict(d) for d in documents]
        
        conn.close()
        
        return jsonify({
            'users': users_list,
            'documents': documents_list,
            'users_count': len(users_list),
            'documents_count': len(documents_list)
        })
        
    except Exception as e:
        return jsonify({'error': f'Debug error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка состояния API"""
    conn = get_db_connection()
    
    # Подсчет пользователей
    users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    # Подсчет документов
    documents_count = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'status': 'healthy',
        'documents_count': documents_count,
        'users_count': users_count,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email и пароль обязательны'}), 400
        
        conn = get_db_connection()
        
        # Проверка существования пользователя
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            conn.close()
            return jsonify({'error': 'Пользователь уже существует'}), 400
        
        # Создание нового пользователя
        user_id = str(uuid.uuid4())
        conn.execute(
            'INSERT INTO users (id, email, password, created_at) VALUES (?, ?, ?, ?)',
            (user_id, email, password, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        print(f"✅ Пользователь зарегистрирован: {email} с ID: {user_id}")
        
        return jsonify({
            'message': 'Пользователь успешно зарегистрирован',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        print(f"❌ Ошибка регистрации: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Авторизация пользователя"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email и пароль обязательны'}), 400
        
        conn = get_db_connection()
        
        # Поиск пользователя
        user = conn.execute(
            'SELECT id, email, password FROM users WHERE email = ?', 
            (email,)
        ).fetchone()
        
        conn.close()
        
        if not user or user['password'] != password:
            return jsonify({'error': 'Неверные учетные данные'}), 401
        
        print(f"✅ Пользователь авторизован: {email} с ID: {user['id']}")
        
        return jsonify({
            'message': 'Успешная авторизация',
            'user_id': user['id'],
            'email': user['email']
        }), 200
        
    except Exception as e:
        print(f"❌ Ошибка авторизации: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'}), 500

@app.route('/api/wizard', methods=['POST'])
def create_standard():
    """Создание стандарта через мастер"""
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        user_id = data.get('user_id', 'anonymous')
        
        print(f"📝 Получены данные мастера: {answers}")
        print(f"📝 User ID: {user_id}")
        
        # Определение типа документа
        doc_type_map = {
            'СОК': 'sok',
            'Рабочая инструкция': 'instruction', 
            'Стандарт процедуры': 'procedure'
        }
        doc_type = doc_type_map.get(answers.get('q1', ''), 'sok')
        
        # Создание заголовка документа
        company_name = answers.get('q2', 'Не указано')
        process_name = answers.get('q4', 'Не указано')
        title = f"{company_name} - {process_name}"
        
        # Сохранение в базу данных
        document_id = str(uuid.uuid4())
        conn = get_db_connection()
        
        conn.execute(
            'INSERT INTO documents (id, user_id, title, type, status, answers, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (document_id, user_id, title, doc_type, 'active', json.dumps(answers), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        print(f"✅ Документ создан: {document_id} для пользователя: {user_id}")
        
        return jsonify({
            'message': 'Стандарт создан успешно',
            'document_id': document_id,
            'title': title,
            'type': doc_type
        }), 201
        
    except Exception as e:
        print(f"❌ Ошибка создания стандарта: {str(e)}")
        return jsonify({'error': 'Ошибка создания стандарта'}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Получение списка документов пользователя"""
    try:
        user_id = request.args.get('user_id')
        
        print(f"📋 Запрос документов для user_id: {user_id}")
        
        conn = get_db_connection()
        
        if user_id:
            # Поиск документов конкретного пользователя
            documents = conn.execute(
                'SELECT id, title, type, status, created_at FROM documents WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            ).fetchall()
        else:
            # Если user_id не указан, возвращаем пустой список
            documents = []
        
        conn.close()
        
        # Преобразование в список словарей
        documents_list = []
        for doc in documents:
            documents_list.append({
                'id': doc['id'],
                'title': doc['title'],
                'type': doc['type'],
                'status': doc['status'],
                'created_at': doc['created_at']
            })
        
        print(f"📋 Найдено документов для пользователя {user_id}: {len(documents_list)}")
        
        return jsonify({
            'documents': documents_list,
            'count': len(documents_list)
        }), 200
        
    except Exception as e:
        print(f"❌ Ошибка получения документов: {str(e)}")
        return jsonify({'error': 'Ошибка получения документов'}), 500

@app.route('/api/export/<document_id>', methods=['GET'])
def export_document(document_id):
    """Экспорт документа в Word формат"""
    try:
        print(f"📤 Запрос экспорта документа: {document_id}")
        
        conn = get_db_connection()
        
        # Получение документа из базы данных
        document = conn.execute(
            'SELECT title, type, answers FROM documents WHERE id = ?',
            (document_id,)
        ).fetchone()
        
        conn.close()
        
        if not document:
            print(f"❌ Документ не найден: {document_id}")
            return jsonify({'error': 'Документ не найден'}), 404
        
        # Парсинг ответов мастера
        answers = json.loads(document['answers'])
        doc_type = document['type']
        
        print(f"📋 Данные документа: {answers}")
        print(f"📋 Тип документа: {doc_type}")
        
        # Подготовка данных для генератора
        base_data = {
            'company_name': answers.get('q2', 'Не указано'),
            'business_area': answers.get('q3', 'Не указано'),
            'process_name': answers.get('q4', 'Не указано'),
            'target_audience': answers.get('q5', 'Не указано'),
            'process_steps': answers.get('q6', 'Не указано'),
            'required_resources': answers.get('q7', 'Не указано'),
            'expected_results': answers.get('q8', 'Не указано')
        }
        
        print(f"📋 Подготовленные данные: {base_data}")
        
        # Генерация документа
        if doc_type == 'sok':
            doc = generator.generate_sok_docx(base_data)
        elif doc_type == 'instruction':
            doc = generator.generate_instruction_docx(base_data)
        elif doc_type == 'procedure':
            doc = generator.generate_procedure_docx(base_data)
        else:
            doc = generator.generate_sok_docx(base_data)
        
        # Создание временного файла
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        temp_file.close()
        
        # Безопасное имя файла
        safe_title = "".join(c for c in document['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}.docx"
        
        print(f"✅ Документ сгенерирован: {filename}")
        
        # Отправка файла с правильными заголовками
        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Принудительные заголовки для правильного скачивания
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Очистка временного файла после отправки
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
        return response
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {str(e)}")
        return jsonify({'error': 'Ошибка экспорта документа'}), 500

if __name__ == '__main__':
    print("🚀 Запуск HOWDO Backend с SQLite базой данных и DEBUG...")
    app.run(host='0.0.0.0', port=5000, debug=True)

