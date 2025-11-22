import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from exam_generator import ExamGenerator
import config

# تمكين اللوجر
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
SCHOOL, QUESTIONS = range(2)

class ExamBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.generator = ExamGenerator()
        self.setup_handlers()
    
    def setup_handlers(self):
        # handlers
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_school)],
                QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_questions)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """بدء المحادثة"""
        user = update.message.from_user
        await update.message.reply_text(
            "🎓 أهلاً بك في بوت احمد خان حيث يمكنك إنشاء نماذج الامتحانات!\n\n"
            "📝 سأساعدك في إنشاء نموذج امتحان بصيغة PDF.\n\n"
            "أولاً، ما هو اسم مدرستك؟ (يمكنك تركها فارغة)"
        )
        return SCHOOL
    
    async def get_school(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """الحصول على اسم المدرسة"""
        context.user_data['school'] = update.message.text
        await update.message.reply_text(
            "ممتاز! الآن أرسل لي أسئلة الامتحان:\n\n"
            "📖 مثال:\n"
            "1. ما هي عاصمة العراق؟\n"
            "2. كم عدد محافظات العراق؟\n"
            "3. اذكر ثلاثة أنهار في العراق.\n\n"
            "يمكنك إرسال جميع الأسئلة في رسالة واحدة"
        )
        return QUESTIONS
    
    async def get_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """معالجة الأسئلة وإنشاء PDF"""
        user = update.message.from_user
        questions_text = update.message.text
        
        # إظهار رسالة "جاري المعالجة"
        processing_msg = await update.message.reply_text("🔄 جاري إنشاء نموذج الامتحان...")
        
        try:
            # إنشاء ملف PDF
            school_name = context.user_data.get('school', '')
            success, result = self.generator.create_exam_pdf(
                questions_text=questions_text,
                school_name=school_name,
                output_file=f"exam_{user.id}.pdf"
            )
            
            if success:
                # إرسال الملف
                with open(result, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"نموذج_امتحان_{user.first_name}.pdf",
                        caption="✅ تم إنشاء نموذج الامتحان بنجاح!"
                    )
                # حذف الملف المؤقت
                os.remove(result)
            else:
                await update.message.reply_text(f"❌ حدث خطأ: {result}")
        
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ حدث خطأ أثناء إنشاء الملف")
        
        finally:
            # حذف رسالة "جاري المعالجة"
            await processing_msg.delete()
        
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """رسالة المساعدة"""
        help_text = """
        📖 كيفية استخدام البوت:
        
        /start - بدء إنشاء نموذج امتحان
        /help - عرض هذه الرسالة
        
        ✨ المميزات:
        - إنشاء نماذج امتحانات PDF
        - دعم النص العربي
        - تنسيق احترافي
        - إضافة اسم المدرسة
        """
        await update.message.reply_text(help_text)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """إلغاء المحادثة"""
        await update.message.reply_text(
            "تم الإلغاء. يمكنك البدء مرة أخرى بـ /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    def run(self):
        """تشغيل البوت"""
        print("🤖 البوت يعمل...")
        self.application.run_polling()

if __name__ == "__main__":
    bot = ExamBot()
    bot.run()
