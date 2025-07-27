from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
import uuid
from datetime import datetime
from final_fixed_document_generator import DocumentGenerator

app = Flask(__name__)
CORS(app)

# Хранилище документов в памяти (для демонстрации)
documents_db = {}
users_db = {}

# Инициализация генератора документов
generator = DocumentGenerator()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка состояния API"""
    return jsonify({
        'status': 'healthy',
        'documents_count': len(documents_db),
        'users_count': len(users_db),
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
        
        if email in users_db:
            return jsonify({'error': 'Пользователь уже существует'}), 400
        
        user_id = str(uuid.uuid4())
        users_db[email] = {
            'id': user_id,
            'email': email,
            'password': password,  # В реальном приложении нужно хешировать
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': 'Пользователь успешно зарегистрирован',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Авторизация пользователя"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email и пароль обязательны'}), 400
        
        user = users_db.get(email)
        if not user or user['password'] != password:
            return jsonify({'error': 'Неверные учетные данные'}), 401
        
        return jsonify({
            'message': 'Успешная авторизация',
            'user_id': user['id'],
            'email': user['email']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wizard', methods=['POST'])
def create_document_from_wizard():
    """Создание документа из мастера (WizardModal.jsx)"""
    try:
        data = request.get_json()
        print(f"[DEBUG] Получены данные от мастера: {data}")  # Отладка
        
        answers = data.get('answers', {})
        user_id = data.get('userId')
        
        if not answers:
            return jsonify({'error': 'Ответы не предоставлены'}), 400
        
        # Определяем тип документа из q1
        document_type = answers.get('q1', 'sok').lower()
        if document_type not in ['сок', 'рабочая инструкция', 'стандарт процедуры']:
            document_type = 'sok'  # По умолчанию СОК
        
        # Создаем документ
        document_id = str(uuid.uuid4())
        
        # ИСПРАВЛЕННЫЙ MAPPING ДАННЫХ ИЗ МАСТЕРА:
        document_data = {
            'id': document_id,
            'user_id': user_id,
            'type': document_type,
            'title': answers.get('q4', 'Новый документ'),  # q4 - процесс
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'answers': answers,
            # Преобразуем answers в структурированные данные:
            'company_name': answers.get('q2', 'Не указано'),      # q2 - компания
            'business_area': answers.get('q3', 'Не указано'),     # q3 - сфера деятельности
            'process_name': answers.get('q4', 'Не указано'),      # q4 - процесс
            'target_audience': answers.get('q5', 'Не указано'),   # q5 - целевая аудитория
            'process_steps': answers.get('q6', 'Не указано'),     # q6 - этапы процесса
            'required_resources': answers.get('q7', 'Не указано'), # q7 - ресурсы
            'expected_results': answers.get('q8', 'Не указано'),  # q8 - результаты
            'creation_date': datetime.now().strftime('%d.%m.%Y')
        }
        
        print(f"[DEBUG] Структурированные данные: {document_data}")  # Отладка
        
        documents_db[document_id] = document_data
        
        return jsonify({
            'message': 'Документ успешно создан',
            'document_id': document_id,
            'title': document_data['title']
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Ошибка создания документа: {str(e)}")  # Отладка
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-standard', methods=['POST'])
def create_standard():
    """Альтернативный endpoint для создания стандарта"""
    return create_document_from_wizard()

@app.route('/api/export/<document_id>', methods=['GET'])
def export_document(document_id):
    """Экспорт документа в Word формате"""
    try:
        print(f"[DEBUG] Экспорт документа ID: {document_id}")  # Отладка
        
        document = documents_db.get(document_id)
        if not document:
            return jsonify({'error': 'Документ не найден'}), 404
        
        print(f"[DEBUG] Найден документ: {document}")  # Отладка
        
        # Подготавливаем данные для генератора
        base_data = {
            'company_name': document.get('company_name', 'Не указано'),
            'business_area': document.get('business_area', 'Не указано'),
            'process_name': document.get('process_name', 'Не указано'),
            'target_audience': document.get('target_audience', 'Не указано'),
            'process_steps': document.get('process_steps', 'Не указано'),
            'required_resources': document.get('required_resources', 'Не указано'),
            'expected_results': document.get('expected_results', 'Не указано'),
            'creation_date': document.get('creation_date', datetime.now().strftime('%d.%m.%Y'))
        }
        
        print(f"[DEBUG] Данные для генератора: {base_data}")  # Отладка
        
        # Определяем тип документа
        doc_type = document.get('type', 'sok').lower()
        
        # Генерируем документ
        if 'сок' in doc_type or doc_type == 'sok':
            doc = generator.generate_sok_docx(base_data)
        elif 'инструкция' in doc_type:
            doc = generator.generate_instruction_docx(base_data)
        elif 'процедура' in doc_type:
            doc = generator.generate_procedure_docx(base_data)
        else:
            doc = generator.generate_sok_docx(base_data)  # По умолчанию СОК
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            doc.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        # Безопасное имя файла
        safe_title = document.get('title', 'документ')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.docx"
        
        print(f"[DEBUG] Отправляем файл: {filename}")  # Отладка
        
        # ИСПРАВЛЕННАЯ ОТПРАВКА ФАЙЛА С ПРАВИЛЬНЫМИ ЗАГОЛОВКАМИ:
        def remove_file(response):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
            return response
        
        # Отправляем файл с принудительными заголовками
        response = send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Добавляем дополнительные заголовки для принудительного скачивания
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache'
        
        # Удаляем временный файл после отправки
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Ошибка экспорта: {str(e)}")  # Отладка
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<document_id>', methods=['GET'])
def preview_document(document_id):
    """Предварительный просмотр документа в HTML"""
    try:
        document = documents_db.get(document_id)
        if not document:
            return jsonify({'error': 'Документ не найден'}), 404
        
        # Подготавливаем данные для генератора (тот же mapping что и в export)
        base_data = {
            'company_name': document.get('company_name', 'Не указано'),
            'business_area': document.get('business_area', 'Не указано'),
            'process_name': document.get('process_name', 'Не указано'),
            'target_audience': document.get('target_audience', 'Не указано'),
            'process_steps': document.get('process_steps', 'Не указано'),
            'required_resources': document.get('required_resources', 'Не указано'),
            'expected_results': document.get('expected_results', 'Не указано'),
            'creation_date': document.get('creation_date', datetime.now().strftime('%d.%m.%Y'))
        }
        
        # Определяем тип документа
        doc_type = document.get('type', 'sok').lower()
        
        # Генерируем HTML
        if 'сок' in doc_type or doc_type == 'sok':
            html_content = generator.generate_sok_html(base_data)
        elif 'инструкция' in doc_type:
            html_content = generator.generate_instruction_html(base_data)
        elif 'процедура' in doc_type:
            html_content = generator.generate_procedure_html(base_data)
        else:
            html_content = generator.generate_sok_html(base_data)
        
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Получение списка документов пользователя"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id обязателен'}), 400
        
        # Фильтруем документы по пользователю
        user_documents = []
        for doc_id, doc_data in documents_db.items():
            if doc_data.get('user_id') == user_id:
                user_documents.append({
                    'id': doc_id,
                    'title': doc_data.get('title', 'Без названия'),
                    'type': doc_data.get('type', 'sok'),
                    'status': doc_data.get('status', 'draft'),
                    'created_at': doc_data.get('created_at'),
                    'company_name': doc_data.get('company_name', 'Не указано')
                })
        
        return jsonify(user_documents), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Получение конкретного документа"""
    try:
        document = documents_db.get(document_id)
        if not document:
            return jsonify({'error': 'Документ не найден'}), 404
        
        return jsonify(document), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Удаление документа"""
    try:
        if document_id not in documents_db:
            return jsonify({'error': 'Документ не найден'}), 404
        
        del documents_db[document_id]
        return jsonify({'message': 'Документ успешно удален'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Запуск HOWDO Backend с исправленным Word экспортом...")
    print("📋 Доступные endpoints:")
    print("  - POST /api/register - регистрация")
    print("  - POST /api/login - авторизация")
    print("  - POST /api/wizard - создание документа из мастера")
    print("  - GET /api/export/<id> - экспорт в Word")
    print("  - GET /api/preview/<id> - предварительный просмотр")
    print("  - GET /api/documents - список документов")
    print("  - GET /api/health - проверка состояния")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

