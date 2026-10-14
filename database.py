import json
import os
import shutil
import threading
import time
from config import DATA_FILE, ADMINS_FILE, SUPER_ADMIN_ID, BACKUPS_DIR

# قفل التزامن لمنع تضارب الكتابة المتزامنة
db_lock = threading.Lock()

def get_initial_categories_data():
    """البيانات الأصلية والرسمية لأقسام وقنوات تطبيق أحمد ال علي TV"""
    return [
        {
            "id": "1",
            "name": "beIN SPORTS",
            "image": "https://f.top4top.io/p_3804lcnvq1.png",
            "channels": [
                {
                    "id": "1",
                    "name": "beIN SPORTS 1 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS1_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "beIN SPORTS 2 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2021/02/beIN_SPORTS2_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "beIN SPORTS 3 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS3_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "4",
                    "name": "beIN SPORTS 4 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS4_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "5",
                    "name": "beIN SPORTS 5 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS5_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "6",
                    "name": "beIN SPORTS 6 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2021/02/beIN_SPORTS6_DIGITAL_Mono-d-1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "7",
                    "name": "beIN SPORTS 7 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS7_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "8",
                    "name": "beIN SPORTS 8 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2023/09/logos-_beINSPORTS8.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "9",
                    "name": "beIN SPORTS 9 HD",
                    "image": "https://assets.bein.com/mena/sites/4/2023/09/logos-_beINSPORTS9.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "10",
                    "name": "beIN SPORTS الإخبارية",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS1_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "11",
                    "name": "beIN SPORTS XTRA",
                    "image": "https://assets.bein.com/mena/sites/4/2015/06/beIN_SPORTS1_DIGITAL_Mono.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "2",
            "name": "قنوات SSC الرياضية",
            "image": "https://j.top4top.io/p_3804z9vu61.png",
            "channels": [
                {
                    "id": "1",
                    "name": "SSC 1 HD",
                    "image": "https://j.top4top.io/p_3804z9vu61.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "SSC 2 HD",
                    "image": "https://j.top4top.io/p_3804z9vu61.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "SSC Extra 1",
                    "image": "https://j.top4top.io/p_3804z9vu61.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "3",
            "name": "قنوات STARZPLAY",
            "image": "https://j.top4top.io/p_3805hdmpb1.png",
            "channels": [
                {
                    "id": "1",
                    "name": "STARZPLAY 1",
                    "image": "https://i.ibb.co/Fk7WLb2G/1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "STARZPLAY 2",
                    "image": "https://i.ibb.co/23B6cTyL/2.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "STARZPLAY 3",
                    "image": "https://i.ibb.co/twz1K5Zq/3.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "4",
            "name": "أبوظبي الرياضية",
            "image": "https://cityupload.io/2026/06/ADMNABUDHABICHANNELY2025MAR-title-logo-en-1-.png",
            "channels": [
                {
                    "id": "1",
                    "name": "أبوظبي الرياضية 1",
                    "image": "https://cityupload.io/2026/06/ABU-DHABI-1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "أبوظبي الرياضية 2",
                    "image": "https://cityupload.io/2026/06/ABU-DHABI-2.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "5",
            "name": "الكأس الرياضية",
            "image": "https://i.ibb.co/p61rC2kZ/logo.png",
            "channels": [
                {
                    "id": "1",
                    "name": "الكأس 1 HD",
                    "image": "https://www.alkass.net/images/new-1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "الكأس 2 HD",
                    "image": "https://www.alkass.net/images/new-2.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "الكأس 3 HD",
                    "image": "https://www.alkass.net/images/new-3.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "4",
                    "name": "الكأس 4 HD",
                    "image": "https://www.alkass.net/images/new-4.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "5",
                    "name": "الكأس 5 HD",
                    "image": "https://www.alkass.net/images/new-5.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "6",
            "name": "دبي الرياضية",
            "image": "https://cityupload.io/2026/06/Dubai-Sports-logo-2023.png",
            "channels": [
                {
                    "id": "1",
                    "name": "دبي الرياضية 1",
                    "image": "https://cityupload.io/2026/06/dub1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "دبي الرياضية 2",
                    "image": "https://cityupload.io/2026/06/dub2.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "7",
            "name": "أون تايم سبورت ON",
            "image": "https://cityupload.io/2026/06/icon_c727b.png",
            "channels": [
                {
                    "id": "1",
                    "name": "أون تايم سبورت 1",
                    "image": "https://cityupload.io/2026/06/ON-SPORTS-1.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "أون تايم سبورت Max",
                    "image": "https://logo.twoapistack.work/img/channels/live_tv_onsport2.png?v=1790526896",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "أون تايم سبورت Plus",
                    "image": "https://logo.twoapistack.work/img/channels/live_tv_onsport3.png?v=1790526908",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "8",
            "name": "قنوات العراق الرياضية",
            "image": "https://cityupload.io/2026/06/logo_35ece.png",
            "channels": [
                {
                    "id": "1",
                    "name": "العراقية الرياضية",
                    "image": "https://cityupload.io/2026/06/iraqiasport.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "العراقية السريانية",
                    "image": "https://cityupload.io/2026/06/whatsapp-image-2024-12-29-at-115110-2-.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "9",
            "name": "باقة MBC وشاهد",
            "image": "https://i.ibb.co/Y4B416tc/logo.png",
            "channels": [
                {
                    "id": "1",
                    "name": "MBC 1",
                    "image": "https://i.ibb.co/Y4B416tc/logo.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "MBC مصر",
                    "image": "https://i.ibb.co/Y4B416tc/logo.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "3",
                    "name": "MBC دراما",
                    "image": "https://i.ibb.co/Y4B416tc/logo.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "4",
                    "name": "MBC Action",
                    "image": "https://i.postimg.cc/fWX9Sscs/djmcy05-8fc80d9d-267c-4001-b342-4046b174b577.png",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "10",
            "name": "قنوات الأخبار العربية",
            "image": "https://i.postimg.cc/JhnM3yZ2/logo.webp",
            "channels": [
                {
                    "id": "1",
                    "name": "الجزيرة الإخبارية",
                    "image": "https://i.postimg.cc/JhnM3yZ2/logo.webp",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                },
                {
                    "id": "2",
                    "name": "العربية الحدث",
                    "image": "https://i.postimg.cc/JhnM3yZ2/logo.webp",
                    "direct_url": "https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8"
                },
                {
                    "id": "3",
                    "name": "سكاي نيوز عربية",
                    "image": "https://i.postimg.cc/JhnM3yZ2/logo.webp",
                    "direct_url": "https://live-hls-web-aja.getaj.net/AJA/01.m3u8"
                }
            ]
        },
        {
            "id": "11",
            "name": "القنوات الإسلامية والقرآن",
            "image": "https://f.top4top.io/p_3804lcnvq1.png",
            "channels": [
                {
                    "id": "1",
                    "name": "قناة القرآن الكريم (مكة)",
                    "image": "https://f.top4top.io/p_3804lcnvq1.png",
                    "direct_url": "https://5a47e923bbde4.streamlock.net/live/quran/playlist.m3u8"
                },
                {
                    "id": "2",
                    "name": "قناة السنة النبوية (المدينة)",
                    "image": "https://f.top4top.io/p_3804lcnvq1.png",
                    "direct_url": "https://5a47e923bbde4.streamlock.net/live/quran/playlist.m3u8"
                }
            ]
        }
    ]

def init_database():
    """تهيئة ملفات قاعدة البيانات إذا لم تكن موجودة مسبقاً"""
    with db_lock:
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(get_initial_categories_data(), f, ensure_ascii=False, indent=2)

        if not os.path.exists(ADMINS_FILE):
            initial_admins = []
            if SUPER_ADMIN_ID:
                initial_admins.append({
                    "user_id": SUPER_ADMIN_ID,
                    "username": "Super Admin",
                    "is_super_admin": True,
                    "can_manage_categories": True,
                    "can_manage_channels": True,
                    "can_manage_admins": True,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            with open(ADMINS_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_admins, f, ensure_ascii=False, indent=2)

# ==============================================================================
# دوال إدارة الأقسام والقنوات
# ==============================================================================

def load_data():
    init_database()
    with db_lock:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return get_initial_categories_data()

def save_data(data):
    with db_lock:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

def get_categories():
    """الحصول على جميع الأقسام مع عدد قنوات كل قسم"""
    data = load_data()
    result = []
    for cat in data:
        result.append({
            "id": str(cat.get("id")),
            "name": cat.get("name", ""),
            "image": cat.get("image", ""),
            "channels_count": len(cat.get("channels", []))
        })
    return result

def get_category(cat_id):
    """الحصول على تفاصيل قسم محدد"""
    data = load_data()
    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            return cat
    return None

def add_category(name, image):
    """إضافة قسم جديد"""
    data = load_data()
    new_id = str(int(time.time()))
    new_category = {
        "id": new_id,
        "name": name.strip(),
        "image": image.strip() if image else "https://f.top4top.io/p_3804lcnvq1.png",
        "channels": []
    }
    data.append(new_category)
    if save_data(data):
        return new_category
    return None

def update_category(cat_id, name=None, image=None):
    """تعديل اسم أو صورة قسم"""
    data = load_data()
    updated = None
    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            if name is not None:
                cat["name"] = name.strip()
            if image is not None:
                cat["image"] = image.strip()
            updated = cat
            break
    if updated and save_data(data):
        return updated
    return None

def delete_category(cat_id):
    """حذف قسم بالكامل مع قنواته"""
    data = load_data()
    original_len = len(data)
    data = [cat for cat in data if str(cat.get("id")) != str(cat_id)]
    if len(data) < original_len:
        save_data(data)
        return True
    return False

def get_channels(cat_id):
    """الحصول على قنوات قسم معين"""
    cat = get_category(cat_id)
    if cat:
        return cat.get("channels", [])
    return []

def get_channel(cat_id, ch_id):
    """الحصول على قناة محددة"""
    channels = get_channels(cat_id)
    for ch in channels:
        if str(ch.get("id")) == str(ch_id):
            return ch
    return None

def add_channel(cat_id, name, direct_url, image=""):
    """إضافة قناة جديدة إلى قسم"""
    data = load_data()
    new_id = str(int(time.time()))
    new_ch = {
        "id": new_id,
        "name": name.strip(),
        "image": image.strip() if image else "https://f.top4top.io/p_3804lcnvq1.png",
        "direct_url": direct_url.strip()
    }
    found = False
    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            if "channels" not in cat:
                cat["channels"] = []
            cat["channels"].append(new_ch)
            found = True
            break
    if found and save_data(data):
        return new_ch
    return None

def update_channel(cat_id, ch_id, name=None, direct_url=None, image=None):
    """تعديل بيانات قناة"""
    data = load_data()
    updated = None
    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            for ch in cat.get("channels", []):
                if str(ch.get("id")) == str(ch_id):
                    if name is not None:
                        ch["name"] = name.strip()
                    if direct_url is not None:
                        ch["direct_url"] = direct_url.strip()
                    if image is not None:
                        ch["image"] = image.strip()
                    updated = ch
                    break
            break
    if updated and save_data(data):
        return updated
    return None

def delete_channel(cat_id, ch_id):
    """حذف قناة من قسم"""
    data = load_data()
    deleted = False
    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            channels = cat.get("channels", [])
            orig_len = len(channels)
            cat["channels"] = [ch for ch in channels if str(ch.get("id")) != str(ch_id)]
            if len(cat["channels"]) < orig_len:
                deleted = True
            break
    if deleted:
        save_data(data)
        return True
    return False

def reset_to_default_data():
    """استعادة البيانات الافتراضية الأصلية"""
    defaults = get_initial_categories_data()
    save_data(defaults)
    return defaults

# ==============================================================================
# دوال إدارة المشرفين والصلاحيات
# ==============================================================================

def load_admins():
    init_database()
    with db_lock:
        try:
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

def save_admins(admins):
    with db_lock:
        try:
            with open(ADMINS_FILE, "w", encoding="utf-8") as f:
                json.dump(admins, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving admins: {e}")
            return False

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مشرفاً معتمداً"""
    if not user_id:
        return False
    if SUPER_ADMIN_ID and int(user_id) == SUPER_ADMIN_ID:
        return True
    admins = load_admins()
    for a in admins:
        if int(a.get("user_id", 0)) == int(user_id):
            return True
    return False

def is_super_admin(user_id):
    """التحقق مما إذا كان المستخدم هو المالك الأعلى"""
    if not user_id:
        return False
    if SUPER_ADMIN_ID and int(user_id) == SUPER_ADMIN_ID:
        return True
    admins = load_admins()
    for a in admins:
        if int(a.get("user_id", 0)) == int(user_id) and a.get("is_super_admin", False):
            return True
    return False

def has_permission(user_id, perm_name):
    """التحقق من امتلاك المشرف لصلاحية معينة"""
    if is_super_admin(user_id):
        return True
    admins = load_admins()
    for a in admins:
        if int(a.get("user_id", 0)) == int(user_id):
            return bool(a.get(perm_name, False))
    return False

def add_admin(user_id, username="", can_manage_categories=True, can_manage_channels=True):
    """إضافة مشرف جديد بصلاحيات محددة"""
    admins = load_admins()
    for a in admins:
        if int(a.get("user_id", 0)) == int(user_id):
            # تحديث الصلاحيات إذا كان موجوداً
            a["username"] = username or a.get("username", "")
            a["can_manage_categories"] = can_manage_categories
            a["can_manage_channels"] = can_manage_channels
            save_admins(admins)
            return a

    new_admin = {
        "user_id": int(user_id),
        "username": username or f"Admin_{user_id}",
        "is_super_admin": False,
        "can_manage_categories": can_manage_categories,
        "can_manage_channels": can_manage_channels,
        "can_manage_admins": False,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    admins.append(new_admin)
    if save_admins(admins):
        return new_admin
    return None

def remove_admin(user_id):
    """حذف مشرف"""
    if SUPER_ADMIN_ID and int(user_id) == SUPER_ADMIN_ID:
        return False  # لا يمكن حذف المالك الأساسي
    admins = load_admins()
    orig_len = len(admins)
    admins = [a for a in admins if int(a.get("user_id", 0)) != int(user_id) or a.get("is_super_admin", False)]
    if len(admins) < orig_len:
        save_admins(admins)
        return True
    return False

# ==============================================================================
# دوال النسخ الاحتياطي والإحصائيات واستيراد M3U
# ==============================================================================

def get_stats():
    """إحصائيات شاملة للأقسام والقنوات والمشرفين"""
    data = load_data()
    admins = load_admins()
    total_cats = len(data)
    total_channels = sum(len(cat.get("channels", [])) for cat in data)
    return {
        "categories_count": total_cats,
        "channels_count": total_channels,
        "admins_count": len(admins)
    }

def create_backup():
    """إنشاء نسخة احتياطية محلية لملف البيانات"""
    init_database()
    try:
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        backup_filename = f"backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(BACKUPS_DIR, backup_filename)
        with db_lock:
            shutil.copy2(DATA_FILE, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def import_json_data(json_str):
    """استعادة قاعدة البيانات من نص JSON كامل مع التحقق من صحته"""
    try:
        parsed = json.loads(json_str)
        if not isinstance(parsed, list):
            return False, "تنسيق البيانات غير صالح (يجب أن يكون مصفوفة أقسام)."
        # التحقق من أن كل عنصر يحتوي على الأقل على id و name
        for item in parsed:
            if not isinstance(item, dict) or "id" not in item or "name" not in item:
                return False, "بعض الأقسام تحتوي على حقول مفقودة."
        create_backup()  # أخذ نسخة احتياطية قبل الاستبدال
        if save_data(parsed):
            return True, "تمت استعادة البيانات بنجاح!"
        return False, "فشل في حفظ البيانات."
    except Exception as e:
        return False, f"خطأ في قراءة ملف JSON: {e}"

def import_m3u_channels_to_category(cat_id, channels_list):
    """إضافة قائمة قنوات مستخرجة من ملف M3U إلى قسم محدد"""
    if not channels_list:
        return 0
    data = load_data()
    added_count = 0
    now = int(time.time())

    for cat in data:
        if str(cat.get("id")) == str(cat_id):
            if "channels" not in cat:
                cat["channels"] = []
            for ch in channels_list:
                name = ch.get("name", "").strip()
                url = ch.get("direct_url", "").strip()
                if not name or not url:
                    continue
                added_count += 1
                new_ch = {
                    "id": str(now + added_count),
                    "name": name,
                    "image": ch.get("image", "").strip() or cat.get("image", ""),
                    "direct_url": url
                }
                cat["channels"].append(new_ch)
            break

    if added_count > 0:
        save_data(data)
    return added_count

def search_channels_global(query):
    """البحث في كافة الأقسام عن القنوات التي تطابق الاسم أو الرابط"""
    query_lower = query.lower().strip()
    data = load_data()
    results = []
    for cat in data:
        cat_name = cat.get("name", "")
        cat_id = str(cat.get("id"))
        for ch in cat.get("channels", []):
            ch_name = ch.get("name", "")
            ch_url = ch.get("direct_url", "")
            if query_lower in ch_name.lower() or query_lower in ch_url.lower():
                results.append({
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "channel_id": str(ch.get("id")),
                    "channel_name": ch_name,
                    "image": ch.get("image", ""),
                    "direct_url": ch_url
                })
    return results

