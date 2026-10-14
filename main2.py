import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# جلب توكن البوت من متغيرات بيئة Railway
TELEGRAM_TOKEN = os.getenv("BOT_TOKENN")

# رابط خادم Ollama الخاص بك على Railway
OLLAMA_URL = "https://Ollama-production-f9db.up.railway.app/api/chat"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا مساعدك البرمجي الذكي، أعمل على خادمك الخاص على Railway. كيف يمكنني مساعدتك اليوم؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # إرسال إشعار للمستخدم بأن النموذج يعالج الكود/السؤال
    status_msg = await update.message.reply_text("جاري التفكير والتوليد...")

    payload = {
        "model": "qwen2.5-coder:1.5b",
        "messages": [
            {
                "role": "system",
                "content": "أنت مساعد ذكاء اصطناعي خبير ومتخصص في كتابة الأكواد، حل المشاكل البرمجية، وبناء المشاريع."
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            ai_reply = response.json()['message']['content']
        else:
            ai_reply = "حدثت مشكلة أثناء معالجة الطلب داخل خادم Ollama."
    except Exception as e:
        ai_reply = f"تعذر الاتصال بالخادم المحلي: {str(e)}"

    # تعديل الرسالة وإرسال الرد النهائي
    await status_msg.edit_text(ai_reply)

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("بوت التليجرام يعالج الطلبات الآن...")
    app.run_polling()
