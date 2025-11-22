import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import re

class ExamGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_arabic_font()
        
    def setup_arabic_font(self):
        try:
            # جرب خطوط عربية مختلفة
            pdfmetrics.registerFont(TTFont('Arabic', 'arial.ttf'))
        except:
            print("⚠️ Using default font - Arabic support may be limited")
    
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
        """تقسيم النص إلى أسئلة بشكل أفضل"""
        # طرق متعددة لتقسيم الأسئلة
        patterns = [
            r'\n\s*\d+[\.\)]\s*',  # 1. أو 1)
            r'\n\s*[-•*]\s*',      # - أو • أو *
            r'\n\s*[٠-٩]+[\.\)]\s*', # الأرقام العربية
        ]
        
        questions = []
        for pattern in patterns:
            questions = re.split(pattern, text)
            if len(questions) > 1:
                break
        
        # تنظيف الأسئلة
        cleaned_questions = []
        for q in questions:
            q_clean = q.strip()
            if q_clean and len(q_clean) > 3:  # تجاهل النصوص القصيرة
                cleaned_questions.append(q_clean)
        
        return cleaned_questions
    
    def create_exam_pdf(self, questions_text, output_file="exam.pdf", 
                       school_name="", ministry_name="وزارة التربية العراقية",
                       exam_title="نموذج امتحان", exam_time="60 دقيقة"):
        
        questions = self.process_questions(questions_text)
        
        if not questions:
            return False, "لم يتم العثور على أسئلة صحيحة"
        
        try:
            doc = SimpleDocTemplate(
                output_file, 
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=20*mm,
                bottomMargin=20*mm,
                title=exam_title
            )
            
            story = []
            
            # إنشاء الرأس مع التنسيق المحسن
            story = self.create_header(story, school_name, ministry_name, exam_title, exam_time)
            
            # إضافة الأسئلة مع تنسيق أفضل
            story = self.add_questions(story, questions)
            
            doc.build(story)
            return True, output_file
            
        except Exception as e:
            return False, f"خطأ في إنشاء PDF: {str(e)}"
    
    def create_header(self, story, school_name, ministry_name, exam_title, exam_time):
        """إنشاء رأس الصفحة مع تنسيق محسن"""
        
        # شعار الوزارة (مركزي)
        ministry_style = ParagraphStyle(
            'MinistryStyle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            textColor='#2E86AB',
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(self.arabic_text(ministry_name), ministry_style))
        
        # خط فاصل
        story.append(Spacer(1, 5))
        
        # اسم المدرسة (إذا موجود)
        if school_name and school_name.strip():
            school_style = ParagraphStyle(
                'SchoolStyle',
                parent=self.styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor='#A23B72',
                spaceAfter=15,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(self.arabic_text(school_name), school_style))
        
        # عنوان الامتحان
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading2'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor='#1B4332',
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(self.arabic_text(exam_title), title_style))
        
        # معلومات الامتحان (الوقت)
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_LEFT,
            textColor='#666666',
            spaceAfter=25
        )
        time_text = f"الوقت: {exam_time}"
        story.append(Paragraph(self.arabic_text(time_text), info_style))
        
        # خط فاصل
        story.append(Spacer(1, 15))
        
        return story
    
    def add_questions(self, story, questions):
        """إضافة الأسئلة مع تنسيق جميل"""
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=13,
            alignment=TA_RIGHT,
            rightIndent=20,
            leftIndent=20,
            spaceAfter=20,
            spaceBefore=10,
            leading=18,
            textColor='#2D3748',
            fontName='Helvetica'
        )
        
        answer_space_style = ParagraphStyle(
            'AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            textColor='#718096',
            borderPadding=5
        )
        
        for i, question in enumerate(questions, 1):
            # رقم السؤال مع تنسيق
            question_number = f"<b>السؤال {i}:</b>"
            story.append(Paragraph(self.arabic_text(question_number), question_style))
            
            # نص السؤال
            story.append(Paragraph(self.arabic_text(question), question_style))
            
            # مساحة للإجابة
            answer_text = "..........................................................................."
            story.append(Paragraph(self.arabic_text(answer_text), answer_space_style))
            story.append(Spacer(1, 25))
            
            # إذا كان عدد الأسئلة كبير، أضف فاصل صفحات
            if i % 5 == 0 and i < len(questions):
                story.append(PageBreak())
                # أعادة إضافة الرأس في الصفحة الجديدة إذا needed
                # يمكن إضافة header هنا إذا تبي
        
        return story

    def add_custom_logo(self, story, logo_path):
        """إضافة شعار مخصص (إذا عندك صورة)"""
        try:
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=50*mm, height=20*mm)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 10))
        except:
            print("⚠️ لم يتمكن من إضافة الشعار")
