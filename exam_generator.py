import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
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
            pdfmetrics.registerFont(TTFont('Arabic', 'arial.ttf'))
        except:
            pass
    
    def arabic_text(self, text):
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    
    def process_questions(self, text):
        questions = re.split(r'\n\s*\d+[\.\)]|\n\s*[-•]', text)
        return [q.strip() for q in questions if q.strip()]
    
    def create_exam_pdf(self, questions_text, output_file="exam.pdf", 
                       school_name="", ministry_name="وزارة التربية العراقية"):
        
        questions = self.process_questions(questions_text)
        
        if not questions:
            return False, "لم يتم العثور على أسئلة"
        
        doc = SimpleDocTemplate(output_file, pagesize=A4, 
                              rightMargin=20*mm, leftMargin=20*mm,
                              topMargin=30*mm, bottomMargin=20*mm)
        
        story = []
        story = self.create_header(story, school_name, ministry_name)
        story = self.add_questions(story, questions)
        
        doc.build(story)
        return True, output_file
    
    def create_header(self, story, school_name, ministry_name):
        ministry_style = ParagraphStyle(
            'MinistryStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        story.append(Paragraph(self.arabic_text(ministry_name), ministry_style))
        
        if school_name:
            school_style = ParagraphStyle(
                'SchoolStyle',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=30
            )
            story.append(Paragraph(self.arabic_text(school_name), school_style))
        
        story.append(Spacer(1, 10))
        return story
    
    def add_questions(self, story, questions):
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_RIGHT,
            rightIndent=10,
            spaceAfter=15,
            leading=16
        )
        
        for i, question in enumerate(questions, 1):
            q_text = f"{i}. {question}"
            story.append(Paragraph(self.arabic_text(q_text), question_style))
            story.append(Spacer(1, 8))
            story.append(Spacer(1, 40))
        
        return story
