"""
Модуль для генерации документов в формате Word (.docx)
"""

import json
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
import re

class DocumentGenerator:
    def __init__(self, templates_dir="/home/ubuntu/templates"):
        self.templates_dir = templates_dir
        self.template_mapping = {
            'sok': 'sok_template.html',
            'instruction': 'instruction_template.html', 
            'procedure': 'procedure_template.html'
        }
    
    def parse_answers(self, answers_json):
        """Парсит ответы пользователя из JSON формата"""
        if isinstance(answers_json, str):
            answers = json.loads(answers_json)
        else:
            answers = answers_json
        
        # Преобразуем в удобный формат
        parsed = {}
        for key, value in answers.items():
            if key.startswith('q'):
                parsed[key] = value
        
        return parsed
    
    def generate_sok_docx(self, answers):
        """Генерирует СОК в формате Word"""
        doc = Document()
        
        # Настройка стилей
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Заголовок
        title = doc.add_heading('СТАНДАРТНАЯ ОПЕРАЦИОННАЯ КАРТА (СОК)', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Основная информация
        doc.add_paragraph()
        info_table = doc.add_table(rows=4, cols=2)
        info_table.style = 'Table Grid'
        
        info_data = [
            ('Компания:', answers.get('q1', 'Не указано')),
            ('Операция:', answers.get('q3', 'Не указано')),
            ('Исполнители:', answers.get('q4', 'Не указано')),
            ('Дата создания:', datetime.now().strftime('%d.%m.%Y'))
        ]
        
        for i, (label, value) in enumerate(info_data):
            info_table.cell(i, 0).text = label
            info_table.cell(i, 1).text = value
        
        # Таблица операций
        doc.add_paragraph()
        doc.add_heading('ПОСЛЕДОВАТЕЛЬНОСТЬ ОПЕРАЦИЙ', 2)
        
        # Парсим шаги из q5
        steps_text = answers.get('q5', '')
        steps = [step.strip() for step in steps_text.split('.') if step.strip()]
        
        if steps:
            ops_table = doc.add_table(rows=len(steps) + 1, cols=4)
            ops_table.style = 'Table Grid'
            ops_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Заголовки таблицы
            headers = ['№', 'Операция', 'Описание', 'Контроль']
            for i, header in enumerate(headers):
                cell = ops_table.cell(0, i)
                cell.text = header
                # Жирный шрифт для заголовков
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Заполнение операций
            for i, step in enumerate(steps, 1):
                ops_table.cell(i, 0).text = str(i)
                ops_table.cell(i, 1).text = f"Шаг {i}"
                ops_table.cell(i, 2).text = step
                ops_table.cell(i, 3).text = "✓"
        
        # Ресурсы и инструменты
        doc.add_paragraph()
        doc.add_heading('НЕОБХОДИМЫЕ РЕСУРСЫ', 2)
        resources_p = doc.add_paragraph()
        resources_p.add_run('Инструменты и материалы: ').bold = True
        resources_p.add_run(answers.get('q6', 'Не указано'))
        
        # Ожидаемые результаты
        doc.add_paragraph()
        doc.add_heading('ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ', 2)
        results_p = doc.add_paragraph()
        results_p.add_run('Результат выполнения: ').bold = True
        results_p.add_run(answers.get('q7', 'Не указано'))
        
        # Подписи
        doc.add_paragraph()
        doc.add_heading('СОГЛАСОВАНИЕ', 2)
        
        signatures_table = doc.add_table(rows=2, cols=3)
        signatures_table.style = 'Table Grid'
        
        # Заголовки подписей
        sig_headers = ['Разработал', 'Проверил', 'Утвердил']
        for i, header in enumerate(sig_headers):
            signatures_table.cell(0, i).text = header
        
        # Поля для подписей
        for i in range(3):
            signatures_table.cell(1, i).text = '________________\n\n(подпись, дата)'
        
        # Футер
        doc.add_paragraph()
        footer_p = doc.add_paragraph('Создано с помощью платформы HowDo')
        footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer_p.runs[0].font.size = Pt(10)
        footer_p.runs[0].font.italic = True
        
        return doc
    
    def generate_instruction_docx(self, answers):
        """Генерирует рабочую инструкцию в формате Word"""
        doc = Document()
        
        # Настройка стилей
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Заголовок
        title = doc.add_heading('РАБОЧАЯ ИНСТРУКЦИЯ', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(answers.get('q3', 'Процесс'), 1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Общие сведения
        doc.add_heading('1. ОБЩИЕ СВЕДЕНИЯ', 2)
        
        general_table = doc.add_table(rows=3, cols=2)
        general_table.style = 'Table Grid'
        
        general_data = [
            ('Компания:', answers.get('q1', 'Не указано')),
            ('Область применения:', answers.get('q2', 'Не указано')),
            ('Целевая аудитория:', answers.get('q4', 'Не указано'))
        ]
        
        for i, (label, value) in enumerate(general_data):
            general_table.cell(i, 0).text = label
            general_table.cell(i, 1).text = value
        
        # Пошаговая инструкция
        doc.add_heading('2. ПОШАГОВАЯ ИНСТРУКЦИЯ', 2)
        
        steps_text = answers.get('q5', '')
        steps = [step.strip() for step in steps_text.split('.') if step.strip()]
        
        if steps:
            for i, step in enumerate(steps, 1):
                step_heading = doc.add_heading(f'Шаг {i}', 3)
                doc.add_paragraph(step)
        
        # Необходимые ресурсы
        doc.add_heading('3. НЕОБХОДИМЫЕ РЕСУРСЫ', 2)
        doc.add_paragraph(answers.get('q6', 'Не указано'))
        
        # Контроль качества
        doc.add_heading('4. КОНТРОЛЬ КАЧЕСТВА', 2)
        doc.add_paragraph(f"Ожидаемый результат: {answers.get('q7', 'Не указано')}")
        
        # Подписи
        doc.add_paragraph()
        doc.add_heading('ЛИСТ СОГЛАСОВАНИЯ', 2)
        
        signatures_table = doc.add_table(rows=2, cols=2)
        signatures_table.style = 'Table Grid'
        
        signatures_table.cell(0, 0).text = 'Разработал'
        signatures_table.cell(0, 1).text = 'Утвердил'
        signatures_table.cell(1, 0).text = '________________\n(подпись, дата)'
        signatures_table.cell(1, 1).text = '________________\n(подпись, дата)'
        
        # Футер
        doc.add_paragraph()
        footer_p = doc.add_paragraph('Создано с помощью платформы HowDo')
        footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer_p.runs[0].font.size = Pt(10)
        footer_p.runs[0].font.italic = True
        
        return doc
    
    def generate_procedure_docx(self, answers):
        """Генерирует стандарт процедуры в формате Word"""
        doc = Document()
        
        # Настройка стилей
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Заголовок
        title = doc.add_heading('СТАНДАРТ ПРОЦЕДУРЫ', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(answers.get('q3', 'Процедура'), 1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Реквизиты документа
        doc.add_paragraph()
        req_table = doc.add_table(rows=3, cols=2)
        req_table.style = 'Table Grid'
        
        req_data = [
            ('Организация:', answers.get('q1', 'Не указано')),
            ('Версия:', '1.0'),
            ('Дата утверждения:', datetime.now().strftime('%d.%m.%Y'))
        ]
        
        for i, (label, value) in enumerate(req_data):
            req_table.cell(i, 0).text = label
            req_table.cell(i, 1).text = value
        
        # Назначение и область применения
        doc.add_heading('1. НАЗНАЧЕНИЕ И ОБЛАСТЬ ПРИМЕНЕНИЯ', 2)
        doc.add_paragraph(f"Настоящая процедура регламентирует порядок выполнения процесса '{answers.get('q3', 'Не указано')}' в {answers.get('q1', 'организации')}.")
        doc.add_paragraph(f"Процедура применяется: {answers.get('q4', 'Не указано')}")
        
        # Ответственность
        doc.add_heading('2. ОТВЕТСТВЕННОСТЬ', 2)
        doc.add_paragraph(f"Ответственные лица: {answers.get('q4', 'Не указано')}")
        
        # Описание процедуры
        doc.add_heading('3. ОПИСАНИЕ ПРОЦЕДУРЫ', 2)
        
        steps_text = answers.get('q5', '')
        steps = [step.strip() for step in steps_text.split('.') if step.strip()]
        
        if steps:
            proc_table = doc.add_table(rows=len(steps) + 1, cols=3)
            proc_table.style = 'Table Grid'
            
            # Заголовки
            headers = ['№', 'Этап процедуры', 'Ответственный']
            for i, header in enumerate(headers):
                cell = proc_table.cell(0, i)
                cell.text = header
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Заполнение этапов
            for i, step in enumerate(steps, 1):
                proc_table.cell(i, 0).text = str(i)
                proc_table.cell(i, 1).text = step
                proc_table.cell(i, 2).text = answers.get('q4', 'Не указано')
        
        # Ресурсы
        doc.add_heading('4. НЕОБХОДИМЫЕ РЕСУРСЫ', 2)
        doc.add_paragraph(answers.get('q6', 'Не указано'))
        
        # Контроль и мониторинг
        doc.add_heading('5. КОНТРОЛЬ И МОНИТОРИНГ', 2)
        doc.add_paragraph(f"Показатели эффективности: {answers.get('q7', 'Не указано')}")
        
        # Лист согласования
        doc.add_paragraph()
        doc.add_heading('ЛИСТ СОГЛАСОВАНИЯ И УТВЕРЖДЕНИЯ', 2)
        
        approval_table = doc.add_table(rows=2, cols=3)
        approval_table.style = 'Table Grid'
        
        approval_headers = ['Разработал', 'Согласовал', 'Утвердил']
        for i, header in enumerate(approval_headers):
            approval_table.cell(0, i).text = header
        
        for i in range(3):
            approval_table.cell(1, i).text = '________________\n(подпись, дата)'
        
        # Футер
        doc.add_paragraph()
        footer_p = doc.add_paragraph('Создано с помощью платформы HowDo')
        footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer_p.runs[0].font.size = Pt(10)
        footer_p.runs[0].font.italic = True
        
        return doc
    
    def generate_docx(self, document_type, answers):
        """Основная функция генерации Word документа"""
        parsed_answers = self.parse_answers(answers)
        
        if document_type == 'sok':
            return self.generate_sok_docx(parsed_answers)
        elif document_type == 'instruction':
            return self.generate_instruction_docx(parsed_answers)
        elif document_type == 'procedure':
            return self.generate_procedure_docx(parsed_answers)
        else:
            raise ValueError(f"Неизвестный тип документа: {document_type}")
    
    def save_docx(self, document_type, answers, output_path):
        """Сохраняет Word документ в файл"""
        doc = self.generate_docx(document_type, answers)
        doc.save(output_path)
        return output_path

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
    
    # Генерируем Word документ для СОК
    output_path = '/home/ubuntu/test_sok.docx'
    generator.save_docx('sok', test_answers, output_path)
    print(f"Word документ сохранен: {output_path}")

