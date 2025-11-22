import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# التوكن من Environment أو افتراضي
BOT_TOKEN = os.getenv('BOT_TOKEN', '7135908560:AAG9SlFOEf55XRdNyz9qKwAfTKliNpUuBjQ')

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
GET_SUBJECT, GET_GRADE, GET_QUESTIONS = range(3)

class ProfessionalExamBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد المحادثة المتقدمة"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                GET_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_subject)],
                GET_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_grade)],
                GET_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_questions)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def start(self, update: Update, context):
        """بدء إنشاء امتحان متكامل"""
        welcome_text = """
🎓 **بوت إنشاء نماذج الامتحانات المتكاملة**

سأنشئ لك امتحاناً كاملاً بنفس تنسيق المدارس العراقية

📚 **لنبدأ بإدخال المعلومات:**
أولاً، ما هي المادة الدراسية؟
(مثال: الاجتماعيات، اللغة العربية، الرياضيات...)
        """
        await update.message.reply_text(welcome_text)
        return GET_SUBJECT
    
    async def get_subject(self, update: Update, context):
        """الحصول على المادة"""
        context.user_data['subject'] = update.message.text
        
        await update.message.reply_text(
            "📅 **ما هي الصف/السنة الدراسية؟**\n"
            "(مثال: السادس الابتدائي، الثالث متوسط...)"
        )
        return GET_GRADE
    
    async def get_grade(self, update: Update, context):
        """الحصول على الصف"""
        context.user_data['grade'] = update.message.text
        
        instructions = """
📝 **الآن أرسل لي محتوى الامتحان الكامل:**

يمكنك نسخ النص من الصور أو الكتابة يدوياً.

🔸 **مثال على التنسيق المطلوب:**
