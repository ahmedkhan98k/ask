import os
from jinja2 import Template
from weasyprint import HTML
import arabic_reshaper
from bidi.algorithm import get_display
import re

class SimpleExamGenerator:
    def __init__(self):
        pass
    
    def arabic_text(self, text):
        """معالجة النص العربي"""
        if not text:
            return ""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    
    def process_questions(self, text):
        """تقسيم النص إلى أسئلة"""
        if not text:
            return []
            
        clean_text = text.strip()
        questions = []
        
        # تقسيم بطرق مختلفة
        patterns = [
            r'\n\s*\d+[\.\)]\s*',
            r'\n\s*[-•*]\s*', 
            r'\n\s*[٠-٩]+[\.\)]\s*',
        ]
        
        for pattern in patterns:
            questions = re.split(pattern, clean_text)
            if len(questions) > 1:
                break
        
        if len(questions) <= 1:
            questions = clean_text.split('\n')
        
        cleaned_questions = []
        for q in questions:
            q_clean = q.strip()
            if (q_clean and len(q_clean) > 2 and
                not q_clean.startswith('العنوان:') and
                not q_clean.startswith('الوقت:') and
                not q_clean.startswith('المدرسة:')):
                cleaned_questions.append(q_clean)
        
        return cleaned_questions
    
    def extract_exam_info(self, text):
        """استخراج معلومات الامتحان"""
        exam_title = "نموذج امتحان"
        exam_time = "٦٠ دقيقة"
        school_name = ""
        
        lines = text.split('\n')
        remaining_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if line_clean.startswith('العنوان:'):
                exam_title = line_clean.replace('العنوان:', '').strip()
            elif line_clean.startswith('الوقت:'):
                exam_time = line_clean.replace('الوقت:', '').strip()
            elif line_clean.startswith('المدرسة:'):
                school_name = line_clean.replace('المدرسة:', '').strip()
            elif line_clean and len(line_clean) > 2:
                remaining_lines.append(line_clean)
        
        return exam_title, exam_time, school_name, '\n'.join(remaining_lines)
    
    def create_exam_pdf(self, questions_text, output_file="exam.pdf", 
                       school_name="", ministry_name="وزارة التربية العراقية"):
        
        # استخراج المعلومات
        exam_title, exam_time, extracted_school, clean_questions = self.extract_exam_info(questions_text)
        final_school_name = school_name if school_name else extracted_school
        questions = self.process_questions(clean_questions)
        
        if not questions:
            return False, "لم يتم العثور على أسئلة صحيحة"
        
        try:
            # قالب HTML بسيط
            html_template = """
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        margin: 40px;
                        background-color: white;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 3px solid #2E86AB;
                        padding-bottom: 15px;
                    }
                    .ministry {
                        font-size: 24px;
                        font-weight: bold;
                        color: #2E86AB;
                        margin-bottom: 10px;
                    }
                    .school {
                        font-size: 20px;
                        font-weight: bold;
                        color: #A23B72;
                        margin-bottom: 10px;
                    }
                    .title {
                        font-size: 28px;
                        font-weight: bold;
                        color: #1B4332;
                        margin-bottom: 15px;
                    }
                    .info {
                        font-size: 16px;
                        color: #666;
                        margin-bottom: 20px;
                        text-align: right;
                    }
                    .question {
                        margin-bottom: 30px;
                        padding: 15px;
                        background-color: #f8f9fa;
                        border-right: 4px solid #4CAF50;
                        border-radius: 5px;
                    }
                    .question-number {
                        font-weight: bold;
                        font-size: 18px;
                        color: #2D3748;
                        margin-bottom: 8px;
                    }
                    .question-text {
                        font-size: 16px;
                        color: #2D3748;
                        margin-bottom: 15px;
                    }
                    .answer-space {
                        background-color: white;
                        border: 1px dashed #ccc;
                        padding: 20px;
                        margin-top: 10px;
                        font-size: 14px;
                        color: #718096;
                        min-height: 60px;
                    }
                    .page-break {
                        page-break-after: always;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="ministry">{{ ministry_name }}</div>
                    {% if school_name %}
                    <div class="school">{{ school_name }}</div>
                    {% endif %}
                    <div class="title">{{ exam_title }}</div>
                    <div class="info">الوقت المخصص: {{ exam_time }} | التاريخ: ........./........./.........</div>
                </div>
                
                {% for question in questions %}
                <div class="question">
                    <div class="question-number">السؤال {{ loop.index }}:</div>
                    <div class="question-text">{{ question }}</div>
                    <div class="answer-space">الإجابة: ....................................................................................................................</div>
                </div>
                
                {% if loop.index % 3 == 0 and not loop.last %}
                <div class="page-break"></div>
                {% endif %}
                {% endfor %}
            </body>
            </html>
            """
            
            # إنشاء HTML
            template = Template(html_template)
            html_content = template.render(
                ministry_name=self.arabic_text(ministry_name),
                school_name=self.arabic_text(final_school_name),
                exam_title=self.arabic_text(exam_title),
                exam_time=self.arabic_text(exam_time),
                questions=[self.arabic_text(q) for q in questions]
            )
            
            # تحويل إلى PDF
            HTML(string=html_content, base_url=__file__).write_pdf(output_file)
            
            return True, output_file
            
        except Exception as e:
            return False, f"خطأ في إنشاء PDF: {str(e)}"
