"""
Модуль для генерации документов на основе шаблонов и ответов пользователя
"""

import json
import os
from datetime import datetime
from jinja2 import Template
import pdfkit
from docx import Document
from docx.shared import Inches
import re

class DocumentGenerator:
    def __init__(self, templates_dir="/home/ubuntu/templates"):
        self.templates_dir = templates_dir
        self.template_mapping = {
            'sok': 'sok_template.html',
            'instruction': 'instruction_template.html', 
            'procedure': 'procedure_template.html'
        }
    
    def load_template(self, document_type):
        """Загружает HTML шаблон для указанного типа документа"""
        template_file = self.template_mapping.get(document_type)
        if not template_file:
            raise ValueError(f"Неизвестный тип документа: {document_type}")
        
        template_path = os.path.join(self.templates_dir, template_file)
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    
    def parse_answers(self, answers_json):
        """Парсит ответы пользователя из JSON формата"""
        if isinstance(answers_json, str):
            answers = json.loads(answers_json)
        else:
            answers = answers_json
        
        # Преобразуем ключи q1, q2, ... в понятные названия
        parsed = {
            'company_name': answers.get('q1', ''),
            'business_area': answers.get('q2', ''),
            'process_name': answers.get('q3', ''),
            'target_audience': answers.get('q4', ''),
            'main_steps': answers.get('q5', ''),
            'required_resources': answers.get('q6', ''),
            'expected_results': answers.get('q7', '')
        }
        
        return parsed
    
    def generate_sok_data(self, parsed_answers):
        """Генерирует данные для шаблона СОК"""
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        # Разбиваем основные шаги на отдельные операции
        steps_text = parsed_answers['main_steps']
        steps_list = [step.strip() for step in re.split(r'[.\n;]', steps_text) if step.strip()]
        
        # Создаем структурированные шаги для таблицы
        structured_steps = []
        for i, step in enumerate(steps_list[:10], 1):  # Максимум 10 шагов
            structured_steps.append({
                'order': f"Шаг {i}",
                'content': step,
                'important_points': "Контроль качества выполнения",
                'tools': "Согласно техкарте",
                'article': "-",
                'quantity': "1"
            })
        
        return {
            'operation_name': parsed_answers['process_name'],
            'operation_number': "001",
            'equipment': parsed_answers['required_resources'],
            'operation_time': "Согласно нормативу",
            'work_position': parsed_answers['target_audience'],
            'steps': structured_steps,
            'safety_risks': "Соблюдение техники безопасности",
            'safety_equipment': "Согласно требованиям ОТ",
            'approval_date': current_date
        }
    
    def generate_instruction_data(self, parsed_answers):
        """Генерирует данные для шаблона рабочей инструкции"""
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        # Разбиваем шаги на подготовительные, основные и завершающие
        steps_text = parsed_answers['main_steps']
        all_steps = [step.strip() for step in re.split(r'[.\n;]', steps_text) if step.strip()]
        
        # Распределяем шаги по категориям
        total_steps = len(all_steps)
        prep_count = max(1, total_steps // 3)
        final_count = max(1, total_steps // 4)
        
        preparation_steps = all_steps[:prep_count]
        main_steps = all_steps[prep_count:-final_count] if final_count < total_steps else all_steps[prep_count:]
        final_steps = all_steps[-final_count:] if final_count < total_steps else ["Завершение процесса"]
        
        # Парсим ресурсы
        resources_text = parsed_answers['required_resources']
        resources_list = [res.strip() for res in re.split(r'[,;\n]', resources_text) if res.strip()]
        resources = []
        for resource in resources_list[:5]:  # Максимум 5 ресурсов
            resources.append({
                'name': resource,
                'quantity': "По потребности",
                'note': "Обязательно"
            })
        
        return {
            'instruction_title': parsed_answers['process_name'],
            'approval_date': current_date,
            'valid_until': datetime(datetime.now().year + 1, 12, 31).strftime("%d.%m.%Y"),
            'purpose': f"Стандартизация процесса {parsed_answers['process_name']} в {parsed_answers['business_area']}",
            'scope': f"Применяется для {parsed_answers['target_audience']}",
            'responsible_persons': parsed_answers['target_audience'],
            'qualification_requirements': "Согласно должностной инструкции",
            'resources': resources,
            'preparation_steps': preparation_steps,
            'main_steps': main_steps,
            'final_steps': final_steps,
            'important_notes': "Строго соблюдать последовательность операций",
            'quality_criteria': parsed_answers['expected_results'],
            'control_methods': "Визуальный контроль, проверка результата",
            'expected_results': parsed_answers['expected_results'],
            'safety_requirements': "Соблюдение требований охраны труда",
            'developer': parsed_answers['company_name'],
            'approver': "Руководитель подразделения"
        }
    
    def generate_procedure_data(self, parsed_answers):
        """Генерирует данные для шаблона стандарта процедуры"""
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        # Создаем шаги процедуры
        steps_text = parsed_answers['main_steps']
        steps_list = [step.strip() for step in re.split(r'[.\n;]', steps_text) if step.strip()]
        
        procedure_steps = []
        for i, step in enumerate(steps_list[:8], 1):  # Максимум 8 шагов
            procedure_steps.append({
                'stage': f"Этап {i}",
                'description': step,
                'responsible': parsed_answers['target_audience'],
                'documents': "Согласно регламенту"
            })
        
        # Матрица ответственности
        responsibilities = [
            {
                'role': 'Исполнитель',
                'responsibility': 'Выполнение процедуры согласно стандарту'
            },
            {
                'role': 'Контролер',
                'responsibility': 'Контроль качества выполнения'
            },
            {
                'role': 'Руководитель',
                'responsibility': 'Общий надзор и утверждение результатов'
            }
        ]
        
        return {
            'company_name': parsed_answers['company_name'],
            'company_details': f"Сфера деятельности: {parsed_answers['business_area']}",
            'document_code': f"СП-{datetime.now().strftime('%Y%m%d')}-001",
            'version': "1.0",
            'approval_date': current_date,
            'procedure_title': parsed_answers['process_name'],
            'purpose': f"Регламентация процесса {parsed_answers['process_name']}",
            'scope': f"Процедура применяется в {parsed_answers['business_area']}",
            'normative_references': "Внутренние стандарты организации",
            'terms_definitions': "Термины используются в соответствии с принятыми в организации определениями",
            'responsibilities': responsibilities,
            'procedure_steps': procedure_steps,
            'special_requirements': "Особые требования отсутствуют",
            'input_documents': "Заявка на выполнение процедуры",
            'output_documents': "Отчет о выполнении процедуры",
            'archiving_rules': "Документы хранятся в течение 3 лет",
            'kpi_indicators': parsed_answers['expected_results'],
            'control_frequency': "Ежемесячно",
            'corrective_actions': "При выявлении несоответствий - немедленная корректировка",
            'developer': parsed_answers['company_name'],
            'coordinator': "Менеджер по качеству",
            'approver': "Генеральный директор",
            'developer_date': current_date,
            'coordinator_date': current_date,
            'approver_date': current_date,
            'creation_date': current_date
        }
    
    def generate_html(self, document_type, answers_json):
        """Генерирует HTML документ на основе типа и ответов"""
        template = self.load_template(document_type)
        parsed_answers = self.parse_answers(answers_json)
        
        if document_type == 'sok':
            data = self.generate_sok_data(parsed_answers)
        elif document_type == 'instruction':
            data = self.generate_instruction_data(parsed_answers)
        elif document_type == 'procedure':
            data = self.generate_procedure_data(parsed_answers)
        else:
            raise ValueError(f"Неподдерживаемый тип документа: {document_type}")
        
        return template.render(**data)
    
    def generate_pdf(self, document_type, answers_json, output_path):
        """Генерирует PDF документ"""
        html_content = self.generate_html(document_type, answers_json)
        
        # Настройки для PDF
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        try:
            pdfkit.from_string(html_content, output_path, options=options)
            return output_path
        except Exception as e:
            # Fallback: сохраняем как HTML если PDF не работает
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return html_path

# Пример использования
if __name__ == "__main__":
    generator = DocumentGenerator()
    
    # Тестовые данные
    test_answers = {
        'q1': 'ООО "Тест Компани"',
        'q2': 'Производство',
        'q3': 'Сборка изделия',
        'q4': 'Рабочие сборочного участка',
        'q5': 'Подготовка рабочего места. Получение деталей. Сборка узла. Контроль качества. Упаковка',
        'q6': 'Отвертка, ключи, измерительные инструменты',
        'q7': 'Качественно собранное изделие без дефектов'
    }
    
    # Генерируем HTML для СОК
    html_content = generator.generate_html('sok', test_answers)
    print("HTML документ сгенерирован успешно!")
