from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from datetime import datetime
from document_generator import DocumentGenerator

app = Flask(__name__)
CORS(app)

# Временная база данных в памяти
users_db = {}
documents_db = {}
document_counter = 1

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if email in users_db:
        return jsonify({'error': 'Пользователь уже существует'}), 400
    
    user_id = len(users_db) + 1
    users_db[email] = {
        'id': user_id,
        'email': email,
        'password': password,
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'message': 'Регистрация успешна',
        'user': {
            'id': user_id,
            'email': email
        }
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = users_db.get(email)
    if not user or user['password'] != password:
        return jsonify({'error': 'Неверные учетные данные'}), 401
    
    return jsonify({
        'message': 'Вход выполнен успешно',
        'user': {
            'id': user['id'],
            'email': user['email']
        }
    })

@app.route('/api/documents', methods=['GET'])
def get_documents():
    # Получаем все документы (в реальном приложении фильтровали бы по пользователю)
    docs_list = []
    for doc_id, doc in documents_db.items():
        docs_list.append({
            'id': doc_id,
            'title': doc['title'],
            'document_type': doc['document_type'],
            'status': doc.get('status', 'Завершено'),
            'created_at': doc['created_at']
        })
    
    return jsonify({'documents': docs_list})

@app.route('/api/wizard', methods=['POST'])
def wizard_endpoint():
    """
    Endpoint для мастера создания стандартов
    Делает то же самое что /api/create-standard
    """
    global document_counter
    
    data = request.get_json()
    
    # Извлекаем данные из запроса
    user_id = data.get('userId')
    answers = data.get('answers', {})
    
    if not user_id:
        return jsonify({'error': 'Пользователь не авторизован'}), 401
    
    # Создаем документ
    doc_id = document_counter
    document_counter += 1
    
    # Определяем тип документа из ответов
    document_type = answers.get('q3', 'sok').lower()
    if document_type not in ['sok', 'instruction', 'procedure']:
        document_type = 'sok'
    
    # Сохраняем документ в базу данных
    documents_db[doc_id] = {
        'id': doc_id,
        'user_id': user_id,
        'title': answers.get('q4', f'Стандарт {doc_id}'),
        'document_type': document_type,
        'answers': answers,
        'status': 'Завершено',
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'message': 'Стандарт создан успешно!',
        'document_id': doc_id
    })

@app.route('/api/create-standard', methods=['POST'])
def create_standard():
    """
    Альтернативный endpoint для создания стандартов
    Дублирует функционал /api/wizard для совместимости
    """
    global document_counter
    
    data = request.get_json()
    
    # Извлекаем данные из запроса
    user_id = data.get('userId')
    answers = data.get('answers', {})
    
    if not user_id:
        return jsonify({'error': 'Пользователь не авторизован'}), 401
    
    # Создаем документ
    doc_id = document_counter
    document_counter += 1
    
    # Определяем тип документа из ответов
    document_type = answers.get('q3', 'sok').lower()
    if document_type not in ['sok', 'instruction', 'procedure']:
        document_type = 'sok'
    
    # Сохраняем документ в базу данных
    documents_db[doc_id] = {
        'id': doc_id,
        'user_id': user_id,
        'title': answers.get('q4', f'Стандарт {doc_id}'),
        'document_type': document_type,
        'answers': answers,
        'status': 'Завершено',
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'message': 'Стандарт создан успешно!',
        'document_id': doc_id
    })

@app.route('/api/export/<int:document_id>', methods=['GET'])
def export_document(document_id):
    # Получаем документ из базы данных
    document = documents_db.get(document_id)
    if not document:
        return jsonify({'error': 'Документ не найден'}), 404
    
    try:
        # Создаем генератор документов
        generator = DocumentGenerator()
        
        # Подготавливаем данные для генерации
        answers = document['answers']
        document_type = document['document_type']
        
        # Базовые данные для всех типов документов
        base_data = {
            'company_name': answers.get('q1', 'Название компании'),
            'business_area': answers.get('q2', 'Сфера деятельности'),
            'process_name': answers.get('q4', 'Название процесса'),
            'target_audience': answers.get('q5', 'Целевая аудитория'),
            'process_steps': answers.get('q6', 'Основные этапы'),
            'required_resources': answers.get('q7', 'Необходимые ресурсы'),
            'expected_results': answers.get('q8', 'Ожидаемые результаты'),
            'creation_date': datetime.now().strftime('%d.%m.%Y'),
            'version': '1.0',
            'author': 'Система HowDo',
            'coordinator': '_________________',
            'coordinator_date': '__.__.____',
            'approver': '_________________',
            'approver_date': '__.__.____'
        }
        
        # Генерируем документ в зависимости от типа
        if document_type == 'sok':
            doc = generator.generate_sok_docx(base_data)
        elif document_type == 'instruction':
            doc = generator.generate_instruction_docx(base_data)
        elif document_type == 'procedure':
            doc = generator.generate_procedure_docx(base_data)
        else:
            return jsonify({'error': 'Неизвестный тип документа'}), 400
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            doc.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        # Формируем безопасное имя файла
        safe_title = ''.join(c for c in document['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title:
            safe_title = f'Документ_{document_id}'
        
        filename = f"{safe_title}.docx"
        
        # Отправляем файл
        def remove_file(response):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return response
        
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        return jsonify({'error': f'Ошибка генерации документа: {str(e)}'}), 500

@app.route('/api/export/<int:document_id>/preview', methods=['GET'])
def preview_document(document_id):
    # Получаем документ из базы данных
    document = documents_db.get(document_id)
    if not document:
        return jsonify({'error': 'Документ не найден'}), 404
    
    try:
        # Создаем генератор документов
        generator = DocumentGenerator()
        
        # Подготавливаем данные для генерации
        answers = document['answers']
        document_type = document['document_type']
        
        # Базовые данные для всех типов документов
        base_data = {
            'company_name': answers.get('q1', 'Название компании'),
            'business_area': answers.get('q2', 'Сфера деятельности'),
            'process_name': answers.get('q4', 'Название процесса'),
            'target_audience': answers.get('q5', 'Целевая аудитория'),
            'process_steps': answers.get('q6', 'Основные этапы'),
            'required_resources': answers.get('q7', 'Необходимые ресурсы'),
            'expected_results': answers.get('q8', 'Ожидаемые результаты'),
            'creation_date': datetime.now().strftime('%d.%m.%Y'),
            'version': '1.0',
            'author': 'Система HowDo',
            'coordinator': '_________________',
            'coordinator_date': '__.__.____',
            'approver': '_________________',
            'approver_date': '__.__.____'
        }
        
        # Генерируем HTML для предварительного просмотра
        if document_type == 'sok':
            html_content = generator.generate_sok_html(base_data)
        elif document_type == 'instruction':
            html_content = generator.generate_instruction_html(base_data)
        elif document_type == 'procedure':
            html_content = generator.generate_procedure_html(base_data)
        else:
            return jsonify({'error': 'Неизвестный тип документа'}), 400
        
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        return jsonify({'error': f'Ошибка генерации предварительного просмотра: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'documents_count': len(documents_db),
        'users_count': len(users_db)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

