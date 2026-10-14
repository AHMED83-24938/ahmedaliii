import sys
import threading
import time
from config import BOT_TOKEN, SUPER_ADMIN_ID, API_HOST, API_PORT, BOT_USERNAME
import database
import api_server
import bot

def run_api_thread():
    """تشغيل خادم الـ API في خيط خلفي"""
    try:
        api_server.start_api_server(API_HOST, API_PORT)
    except Exception as e:
        print(f"❌ خطأ في تشغيل خادم الـ API: {e}")

def main():
    print("=" * 65)
    print("  📺 نظام إدارة وتحكم تطبيق أحمد ال علي TV (Bot & API Server) 📺")
    print("=" * 65)

    # 1. تهيئة قاعدة البيانات والتأكد من البيانات
    database.init_database()
    stats = database.get_stats()
    print(f"📊 قاعدة البيانات جاهزة: {stats['categories_count']} قسم | {stats['channels_count']} قناة بث")

    # 2. تشغيل خادم الـ API في الخلفية
    api_thread = threading.Thread(target=run_api_thread, daemon=True)
    api_thread.start()
    time.sleep(1)

    print("-" * 65)
    print(f"📡 رابط الـ API المباشر لتطبيق أندرويد: http://{API_HOST}:{API_PORT}/api/data")
    print(f"🔗 فحص حالة السيرفر: http://{API_HOST}:{API_PORT}/api/status")
    print("-" * 65)

    # 3. التحقق من إعدادات التيليجرام
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        print("⚠️ تنبيه: لم يتم تعيين BOT_TOKEN بعد في ملف .env!")
        print("📝 الخطوات المطلوبة للبدء:")
        print("   1. افتح ملف .env في مجلد tv_backend")
        print("   2. ضع توكن البوت: BOT_TOKEN=توكن_البوت_هنا")
        print("   3. ضع معرف حسابك: ADMIN_ID=معرفك_الرقمي_هنا")
        print("   4. أعد تشغيل السكربت: python3 main.py")
        print("\n⏳ خادم الـ API يعمل حالياً في الخلفية لخدمة التطبيق... اضغط Ctrl+C للإيقاف.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 تم إيقاف النظام.")
            sys.exit(0)
    else:
        print(f"🤖 جاري تشغيل بوت تيليجرام (@{BOT_USERNAME})...")
        print(f"👑 المشرف الرئيسي (Super Admin ID): {SUPER_ADMIN_ID if SUPER_ADMIN_ID else 'غير محدد (أي مشرف معتمد)'}")
        print("=" * 65)
        try:
            bot.start_bot()
        except KeyboardInterrupt:
            print("\n👋 تم إيقاف النظام.")
            sys.exit(0)

if __name__ == "__main__":
    main()
