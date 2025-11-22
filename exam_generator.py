import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import arabic_reshaper
from bidi.algorithm import get_display
import re

class ExamGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_arabic_font()
        
    def setup_arabic_font(self):
        """إعداد الخط العربي - استخدام خط افتراضي"""
        try:
            # استخدام الخط الافتراضي مع دعم العربي
            pdfmetrics.registerFont(TTFont('ArabicFont', 'arial.ttf'))
        except:
            # إذا ما نجح، استخدم الخط الافتراضي
            print("Using default font")
    
    def arabic_text(self, text):
        """معالجة النص العربي للتنسيق الصحيح"""
        if not text:
            return ""
        try:
            # معالجة النص العربي
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            print(f"Error in arabic text processing: {e}")
            return text
    
    def process_questions(self, text):
        """تقسيم النص إلى أسئلة بشكل صحيح"""
        if not text:
            return []
            
        # تنظيف النص أولاً
        clean_text = text.strip()
        
        # طرق متعددة لتقسيم الأسئلة
        patterns = [
            r'\n\s*\d+[\.\)]\s*',      # 1. أو 1)
            r'\n\s*[-•*]\s*',          # - أو • أو *
            r'\n\s*[٠-٩]+[\.\)]\s*',   # الأرقام العربية
            r'\n\s*[a-zA-Z][\.\)]\s*', # a. أو A)
        ]
        
        questions = []
        for pattern in patterns:
            questions = re.split(pattern, clean_text)
            if len(questions) > 1:  # إذا وجد تقسيم ناجح
                break
        
        # إذا ما نجح التقسيم، استخدم السطور كأسئلة
        if len(questions) <= 1:
            questions = clean_text.split('\n')
        
        # تنظيف الأسئلة
        cleaned_questions = []
        for q in questions:
            q_clean = q.strip()
            # تجاهل الأسطر الفارغة والقصيرة جداً
            if (q_clean and 
                len(q_clean) > 2 and 
                not q_clean.startswith('العنوان:') and 
                not q_clean.startswith('الوقت:')):
                cleaned_questions.append(q_clean)
        
        return cleaned_questions
    
    def extract_exam_info(self, text):
        """استخراج معلومات الامتحان من النص"""
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
        
        # استخراج معلومات الامتحان من النص
        exam_title, exam_time, extracted_school, clean_questions = self.extract_exam_info(questions_text)
        
        # استخدام اسم المدرسة من الإدخال أو من النص
        final_school_name = school_name if school_name else extracted_school
        
        questions = self.process_questions(clean_questions)
        
        if not questions:
            return False, "لم يتم العثور على أسئلة صحيحة"
        
        try:
            doc = SimpleDocTemplate(
                output_file, 
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )
            
            story = []
            
            # إنشاء الرأس
            story = self.create_header(story, final_school_name, ministry_name, exam_title, exam_time)
            
            # إضافة الأسئلة
            story = self.add_questions(story, questions)
            
            doc.build(story)
            return True, output_file
            
        except Exception as e:
            return False, f"خطأ في إنشاء PDF: {str(e)}"
    
    def create_header(self, story, school_name, ministry_name, exam_title, exam_time):
        """إنشاء رأس الصفحة"""
        
        # وزارة التربية
        ministry_style = ParagraphStyle(
            'MinistryStyle',
            parent=self.styles['Normal'],
            fontSize=16,
            alignment=TA_CENTER,
            textColor=HexColor('#2E86AB'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(self.arabic_text(ministry_name), ministry_style))
        
        # اسم المدرسة (إذا موجود)
        if school_name and school_name.strip():
            school_style = ParagraphStyle(
                'SchoolStyle',
                parent=self.styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=HexColor('#A23B72'),
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(self.arabic_text(school_name), school_style))
        
        # عنوان الامتحان
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Normal'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=HexColor('#1B4332'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(self.arabic_text(exam_title), title_style))
        
        # معلومات الامتحان في جدول
        info_data = [
            [self.arabic_text('الوقت المخصص:'), self.arabic_text(exam_time)],
            [self.arabic_text('تاريخ الامتحان:'), self.arabic_text('........./........./.........')]
        ]
        
        info_table = Table(info_data, colWidths=[60*mm, 60*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def add_questions(self, story, questions):
        """إضافة الأسئلة مع التنسيق الصحيح"""
        
        # نمط السؤال
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=13,
            alignment=TA_RIGHT,
            rightIndent=10,
            leftIndent=10,
            spaceAfter=12,
            spaceBefore=8,
            leading=20,
            textColor=HexColor('#2D3748'),
            fontName='Helvetica'
        )
        
        # نمط مساحة الإجابة
        answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_RIGHT,
            textColor=HexColor('#718096'),
            borderPadding=8,
            backColor=HexColor('#F7FAFC')
        )
        
        for i, question in enumerate(questions, 1):
            if not question.strip():
                continue
                
            # رقم السؤال
            question_wrapper = f"<b>السؤال {i}:</b><br/>{question}"
            
            # إضافة السؤال
            story.append(Paragraph(self.arabic_text(question_wrapper), question_style))
            
            # مساحة للإجابة
            answer_table_data = [[self.arabic_text("الإجابة: ................................................................................................................................................")]]
            answer_table = Table(answer_table_data, colWidths=[160*mm])
            answer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#718096')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F7FAFC')),
            ]))
            
            story.append(answer_table)
            story.append(Spacer(1, 25))
        
        return story
