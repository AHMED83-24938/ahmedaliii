import os

def _load_env_file(filepath):
    """تحميل متغيرات البيئة من ملف محدد دون الاعتماد على مكتبات خارجية"""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"Warning loading env file {filepath}: {e}")

# مسارات المشروع الأساسية
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

# محاولة استخدام python-dotenv إن وجدت، أو القارئ المدمج
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
except ImportError:
    pass

_load_env_file(ENV_FILE)

# ==============================================================================
# إعدادات البوت والتحكم
# ==============================================================================

# توكن بوت تيليجرام (احصل عليه من @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# معرف حسابك في تيليجرام (Super Admin) - احصل عليه من @userinfobot
raw_admin = os.getenv("ADMIN_ID") or os.getenv("SUPER_ADMIN_ID", "0")
try:
    SUPER_ADMIN_ID = int(str(raw_admin).strip())
except (ValueError, TypeError):
    SUPER_ADMIN_ID = 0

ADMIN_ID = SUPER_ADMIN_ID

# يوزرنيم البوت (بدون @) لربطه بالتطبيق
BOT_USERNAME = os.getenv("BOT_USERNAME", "AhmedAlAliTVBot").strip().replace("@", "")

# ==============================================================================
# إعدادات خادم الـ API للمزامنة مع تطبيق أندرويد
# ==============================================================================
API_HOST = os.getenv("HOST", "0.0.0.0").strip()
API_PORT = int(os.getenv("PORT", "8080"))

# المسار العام للسيرفر (اختياري، مثلاً رابط ngrok أو السيرفر السحابي)
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")

# مسارات ملفات البيانات
DATA_FILE = os.path.join(BASE_DIR, "data.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

if not os.path.exists(BACKUPS_DIR):
    try:
        os.makedirs(BACKUPS_DIR, exist_ok=True)
    except Exception:
        pass
