import os
import re
import time
import telebot
from telebot import types
import database
import stream_checker
from config import BOT_TOKEN, SUPER_ADMIN_ID, ADMIN_ID, BOT_USERNAME, API_HOST, API_PORT, PUBLIC_API_URL

DUMMY_TOKEN = "1234567890:AAPlaceholderTokenForAhmedAlAliTV"

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    print("⚠️ ملاحظة: BOT_TOKEN غير محدد بعد في ملف .env (يرجى إدخاله لتشغيل البوت)")
    active_token = DUMMY_TOKEN
else:
    active_token = BOT_TOKEN

bot = telebot.TeleBot(active_token, parse_mode="HTML")

# ذاكرة الحالة المؤقتة للمستخدمين أثناء إدخال البيانات
user_states = {}

# ==============================================================================
# دوال التحقق المساعدة
# ==============================================================================

def check_auth(user_id):
    """التحقق من صلاحيات المشرف"""
    if not user_id:
        return False
    # إذا لم يكن هناك سوبر أدمن محدد مسبقاً في ملف .env، نجعل أول من يرسل رسالة هو الأدمن
    if not SUPER_ADMIN_ID:
        return True
    return database.is_admin(user_id)

def send_unauthorized(chat_id, user_id):
    text = (
        "⛔ <b>عذراً، الوصول مرفوض!</b>\n\n"
        "هذا البوت مخصص لإدارة تطبيق <b>أحمد ال علي TV</b> للمشرفين المعتمدين فقط.\n\n"
        f"🆔 معرف حسابك (Telegram ID): <code>{user_id}</code>\n"
        "يرجى تزويد مالك التطبيق بهذا المعرف لمنحك صلاحيات الإدارة."
    )
    bot.send_message(chat_id, text)

# ==============================================================================
# القائمة الرئيسية ولوحة التحكم
# ==============================================================================

def get_main_menu_keyboard(is_super):
    markup = types.InlineKeyboardMarkup(row_width=2)
    b_cats = types.InlineKeyboardButton("📂 إدارة الأقسام", callback_data="cats_list")
    b_chans = types.InlineKeyboardButton("📺 إدارة القنوات", callback_data="chans_select_cat")
    b_add_cat = types.InlineKeyboardButton("➕ إضافة قسم", callback_data="cat_add")
    b_add_chan = types.InlineKeyboardButton("➕ إضافة قناة", callback_data="chan_add_select_cat")
    b_test = types.InlineKeyboardButton("🔗 فحص رابط بث", callback_data="test_stream_prompt")
    b_backup = types.InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="backup_menu")
    b_api = types.InlineKeyboardButton("⚙️ إعدادات الـ API والتطبيق", callback_data="api_info")

    markup.add(b_cats, b_chans)
    markup.add(b_add_cat, b_add_chan)
    markup.add(b_test, b_backup)

    if is_super:
        b_admins = types.InlineKeyboardButton("👥 إدارة المشرفين", callback_data="admins_menu")
        markup.add(b_admins, b_api)
    else:
        markup.add(b_api)

    return markup

@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    user_id = message.from_user.id
    if not check_auth(user_id):
        send_unauthorized(message.chat.id, user_id)
        return

    # مسح أي حالة سابقة
    user_states.pop(user_id, None)

    stats = database.get_stats()
    is_super = database.is_super_admin(user_id)

    welcome_text = (
        "📺 <b>لوحة تحكم تطبيق أحمد ال علي TV</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"مرحباً بك <b>{message.from_user.first_name}</b> في نظام الإدارة المباشر.\n\n"
        "📊 <b>إحصائيات النظام الحالية:</b>\n"
        f"• 📁 الأقسام: <b>{stats['categories_count']}</b> قسم\n"
        f"• 📡 القنوات: <b>{stats['channels_count']}</b> قناة بث\n"
        f"• 👥 المشرفين: <b>{stats['admins_count']}</b> مشرف\n\n"
        "💡 <i>ملاحظة سريعة:</i> يمكنك إرسال أي رابط بث (M3U8 أو M3U أو JS) مباشرة في الشات وسيظهر لك خيار ربطه بقناة أو قسم فوراً!"
    )

    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard(is_super))

# ==============================================================================
# معالجة الروابط المباشرة وملفات M3U المرسلة في الشات
# ==============================================================================

@bot.message_handler(content_types=["document"])
def handle_documents(message):
    user_id = message.from_user.id
    if not check_auth(user_id):
        send_unauthorized(message.chat.id, user_id)
        return

    doc = message.document
    file_name = doc.file_name.lower()

    # إذا كان ملف نسخة احتياطية JSON
    if file_name.endswith(".json"):
        msg = bot.send_message(message.chat.id, "⏳ جاري قراءة ملف النسخة الاحتياطية...")
        try:
            file_info = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            content_str = downloaded.decode("utf-8")
            ok, res_msg = database.import_json_data(content_str)
            bot.delete_message(message.chat.id, msg.message_id)
            if ok:
                bot.send_message(message.chat.id, f"✅ <b>نجحت الاستعادة:</b>\n{res_msg}", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
            else:
                bot.send_message(message.chat.id, f"❌ <b>فشلت الاستعادة:</b>\n{res_msg}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ أثناء معالجة الملف: {e}")
        return

    # إذا كان ملف قائمة تشغيل M3U أو M3U8
    if file_name.endswith(".m3u") or file_name.endswith(".m3u8"):
        msg = bot.send_message(message.chat.id, "⏳ جاري تحليل ملف قائمة التشغيل M3U...")
        try:
            file_info = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            content_str = downloaded.decode("utf-8", errors="ignore")
            parsed_channels = stream_checker.parse_m3u_text(content_str)
            bot.delete_message(message.chat.id, msg.message_id)

            if not parsed_channels:
                bot.send_message(message.chat.id, "⚠️ لم يتم العثور على أي قنوات صالحة داخل ملف M3U.")
                return

            # حفظ القنوات مؤقتاً في الذاكرة
            user_states[user_id] = {
                "action": "import_m3u_file",
                "channels": parsed_channels
            }

            cats = database.get_categories()
            markup = types.InlineKeyboardMarkup(row_width=2)
            for c in cats:
                markup.add(types.InlineKeyboardButton(f"📂 {c['name']} ({c['channels_count']})", callback_data=f"m3u_cat_import:{c['id']}"))
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))

            text = (
                f"📑 <b>تم استخراج {len(parsed_channels)} قناة من ملف M3U بنجاح!</b>\n\n"
                "اختر القسم الذي تريد استيراد هذه القنوات إليه:"
            )
            bot.send_message(message.chat.id, text, reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ في معالجة الملف: {e}")
        return

@bot.message_handler(func=lambda m: m.text and ("http://" in m.text or "https://" in m.text or "rtmp://" in m.text))
def handle_stream_links(message):
    user_id = message.from_user.id
    if not check_auth(user_id):
        send_unauthorized(message.chat.id, user_id)
        return

    # استخراج الرابط
    urls = re.findall(r'(?:http[s]?|rtmp)://[^\s<>"]+', message.text)
    if not urls:
        return
    url = urls[0].strip()

    status_msg = bot.send_message(message.chat.id, f"🔍 <b>جاري فحص الرابط:</b>\n<code>{url}</code>\n\nيرجى الانتظار ثوانٍ معدودة...")

    # فحص صحة الرابط ونوعه
    check_result = stream_checker.check_stream_url(url)
    bot.delete_message(message.chat.id, status_msg.message_id)

    # حفظ الرابط في حالة المستخدم الحالية
    user_states[user_id] = {
        "pending_url": url,
        "link_type": check_result.get("type", "unknown")
    }

    # تجهيز أزرار الأقسام لاختيار القسم المطلوب
    cats = database.get_categories()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for c in cats:
        btn_text = f"📂 {c['name']} ({c['channels_count']})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"link_cat_sel:{c['id']}"))
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="main_menu"))

    type_badge = {
        "m3u8": "🟢 HLS M3U8",
        "m3u": "📑 M3U Playlist",
        "js": "⚡ JavaScript Stream",
        "direct": "🎬 Direct Stream (TS/MP4)",
        "unknown": "🔗 رابط عام"
    }.get(check_result.get("type"), "🔗 رابط")

    status_badge = "✅ شغال ومستجيب" if check_result.get("is_valid") else "⚠️ قد يكون معطلاً أو محجوباً"

    res_text = (
        f"📡 <b>نتيجة فحص الرابط:</b>\n"
        f"• النوع: <b>{type_badge}</b>\n"
        f"• الحالة: <b>{status_badge}</b> ({check_result.get('latency_ms', 0)}ms)\n"
        f"• الرابط:\n<code>{url}</code>\n\n"
        "👇 <b>اختر القسم الذي تريد ربط هذا البث به داخل تطبيق أحمد ال علي TV:</b>"
    )

    bot.send_message(message.chat.id, res_text, reply_markup=markup)

# ==============================================================================
# معالجة نقرات الأزرار (Callback Queries)
# ==============================================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    if not check_auth(user_id):
        bot.answer_callback_query(call.id, "⛔ ليس لديك صلاحية المشرف!", show_alert=True)
        return

    data = call.data
    chat_id = call.message.chat.id

    # 1. القائمة الرئيسية
    if data == "main_menu":
        user_states.pop(user_id, None)
        stats = database.get_stats()
        is_super = database.is_super_admin(user_id)
        text = (
            "📺 <b>لوحة تحكم تطبيق أحمد ال علي TV</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• 📁 الأقسام: <b>{stats['categories_count']}</b> | 📡 القنوات: <b>{stats['channels_count']}</b>"
        )
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=get_main_menu_keyboard(is_super))
        except Exception:
            bot.send_message(chat_id, text, reply_markup=get_main_menu_keyboard(is_super))
        return

    # 2. عرض قائمة الأقسام
    if data == "cats_list":
        cats = database.get_categories()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for c in cats:
            markup.add(types.InlineKeyboardButton(f"📂 {c['name']} ({c['channels_count']})", callback_data=f"cat_view:{c['id']}"))
        markup.add(types.InlineKeyboardButton("➕ إضافة قسم جديد", callback_data="cat_add"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu"))

        text = "📁 <b>أقسام تطبيق أحمد ال علي TV:</b>\nاضغط على أي قسم لإدارته، تعديله، أو مشاهدة قنواته:"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 3. عرض تفاصيل قسم محدد
    if data.startswith("cat_view:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        if not cat:
            bot.answer_callback_query(call.id, "⚠️ هذا القسم غير موجود أو تم حذفه!", show_alert=True)
            return

        ch_count = len(cat.get("channels", []))
        text = (
            f"📂 <b>تفاصيل القسم:</b>\n"
            f"• الاسم: <b>{cat.get('name')}</b>\n"
            f"• المعرف (ID): <code>{cat.get('id')}</code>\n"
            f"• عدد القنوات: <b>{ch_count}</b> قناة\n"
            f"• رابط الشعار:\n<code>{cat.get('image')}</code>\n"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        b_chans = types.InlineKeyboardButton(f"📺 قنوات القسم ({ch_count})", callback_data=f"chans_list:{cat_id}")
        b_add_ch = types.InlineKeyboardButton("➕ إضافة قناة بالقسم", callback_data=f"chan_add:{cat_id}")
        b_rename = types.InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"cat_edit_name:{cat_id}")
        b_reimg = types.InlineKeyboardButton("🖼️ تغيير الشعار", callback_data=f"cat_edit_img:{cat_id}")
        b_del = types.InlineKeyboardButton("🗑️ حذف القسم", callback_data=f"cat_del_ask:{cat_id}")
        b_back = types.InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="cats_list")

        markup.add(b_chans)
        markup.add(b_add_ch)
        markup.add(b_rename, b_reimg)
        markup.add(b_del)
        markup.add(b_back)

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 4. طلب تأكيد حذف قسم
    if data.startswith("cat_del_ask:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        if not cat:
            return
        ch_count = len(cat.get("channels", []))
        text = (
            f"⚠️ <b>تأكيد حذف القسم!</b>\n\n"
            f"هل أنت متأكد من حذف قسم <b>{cat.get('name')}</b>؟\n"
            f"سيتم حذف جميع القنوات التابعة له ({ch_count} قناة) نهائياً من التطبيق!"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🗑️ نعم، احذف القسم", callback_data=f"cat_del_confirm:{cat_id}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data=f"cat_view:{cat_id}")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data.startswith("cat_del_confirm:"):
        cat_id = data.split(":", 1)[1]
        if database.delete_category(cat_id):
            bot.answer_callback_query(call.id, "✅ تم حذف القسم بنجاح!")
            cats = database.get_categories()
            markup = types.InlineKeyboardMarkup(row_width=2)
            for c in cats:
                markup.add(types.InlineKeyboardButton(f"📂 {c['name']} ({c['channels_count']})", callback_data=f"cat_view:{c['id']}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu"))
            bot.edit_message_text("✅ <b>تم حذف القسم وجميع قنواته بنجاح!</b>\nتظهر النتيجة في التطبيق فوراً.", chat_id, call.message.message_id, reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ فشل في حذف القسم!", show_alert=True)
        return

    # 5. تعديل اسم قسم
    if data.startswith("cat_edit_name:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        user_states[user_id] = {"action": "waiting_cat_new_name", "cat_id": cat_id}
        msg = bot.send_message(chat_id, f"✏️ اكتب الاسم الجديد لقسم <b>{cat.get('name')}</b>:")
        bot.register_next_step_handler(msg, step_update_cat_name)
        return

    # 6. تعديل صورة قسم
    if data.startswith("cat_edit_img:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        user_states[user_id] = {"action": "waiting_cat_new_img", "cat_id": cat_id}
        msg = bot.send_message(chat_id, f"🖼️ أرسل رابط الصورة الجديد لقسم <b>{cat.get('name')}</b> أو أرسل صورة مباشرة:")
        bot.register_next_step_handler(msg, step_update_cat_image)
        return

    # 7. إضافة قسم جديد
    if data == "cat_add":
        user_states[user_id] = {"action": "waiting_new_cat_name"}
        msg = bot.send_message(chat_id, "➕ <b>إضافة قسم جديد:</b>\n\nاكتب اسم القسم المراد إنشاؤه (مثال: قنوات وثائقية):")
        bot.register_next_step_handler(msg, step_add_cat_name)
        return

    # 8. استعراض قنوات قسم
    if data.startswith("chans_list:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        if not cat:
            return
        channels = cat.get("channels", [])
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in channels:
            markup.add(types.InlineKeyboardButton(f"📺 {ch.get('name')}", callback_data=f"chan_view:{cat_id}:{ch.get('id')}"))
        markup.add(types.InlineKeyboardButton("➕ إضافة قناة في هذا القسم", callback_data=f"chan_add:{cat_id}"))
        markup.add(types.InlineKeyboardButton(f"🔙 رجوع لقسم {cat.get('name')}", callback_data=f"cat_view:{cat_id}"))

        text = f"📺 <b>قنوات قسم {cat.get('name')}:</b> (المجموع: {len(channels)})\nاضغط على أي قناة لمعاينة رابطها، تعديلها، أو فحص حالة البث:"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data == "chans_select_cat" or data == "chan_add_select_cat":
        is_adding = (data == "chan_add_select_cat")
        cats = database.get_categories()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for c in cats:
            dest = f"chan_add:{c['id']}" if is_adding else f"chans_list:{c['id']}"
            markup.add(types.InlineKeyboardButton(f"📂 {c['name']} ({c['channels_count']})", callback_data=dest))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu"))
        title = "➕ <b>اختر القسم الذي تريد إضافة قناة إليه:</b>" if is_adding else "📺 <b>اختر القسم لاستعراض قنواته:</b>"
        bot.edit_message_text(title, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 9. عرض تفاصيل قناة
    if data.startswith("chan_view:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        cat = database.get_category(cat_id)
        if not ch or not cat:
            bot.answer_callback_query(call.id, "⚠️ لم يتم العثور على القناة!", show_alert=True)
            return

        text = (
            f"📺 <b>تفاصيل القناة:</b>\n"
            f"• الاسم: <b>{ch.get('name')}</b>\n"
            f"• القسم: <b>{cat.get('name')}</b>\n"
            f"• معرف القناة: <code>{ch.get('id')}</code>\n\n"
            f"📡 <b>رابط البث المباشر:</b>\n<code>{ch.get('direct_url')}</code>\n\n"
            f"🖼️ <b>رابط الشعار:</b>\n<code>{ch.get('image')}</code>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        b_test = types.InlineKeyboardButton("🧪 فحص حالة البث", callback_data=f"chan_test:{cat_id}:{ch_id}")
        b_rename = types.InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"chan_edit_name:{cat_id}:{ch_id}")
        b_reurl = types.InlineKeyboardButton("🔗 تعديل رابط البث", callback_data=f"chan_edit_url:{cat_id}:{ch_id}")
        b_reimg = types.InlineKeyboardButton("🖼️ تعديل الصورة", callback_data=f"chan_edit_img:{cat_id}:{ch_id}")
        b_del = types.InlineKeyboardButton("🗑️ حذف القناة", callback_data=f"chan_del_ask:{cat_id}:{ch_id}")
        b_back = types.InlineKeyboardButton(f"🔙 رجوع لقنوات {cat.get('name')}", callback_data=f"chans_list:{cat_id}")

        markup.add(b_test)
        markup.add(b_rename, b_reurl)
        markup.add(b_reimg, b_del)
        markup.add(b_back)

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 10. فحص رابط بث قناة معينة
    if data.startswith("chan_test:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        if not ch:
            return
        bot.answer_callback_query(call.id, "⏳ جاري فحص البث...")
        url = ch.get("direct_url", "")
        res = stream_checker.check_stream_url(url)
        msg_alert = f"النتيجة: {res.get('message')} ({res.get('latency_ms', 0)}ms)"
        bot.answer_callback_query(call.id, msg_alert, show_alert=True)
        return

    # 11. حذف قناة
    if data.startswith("chan_del_ask:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        if not ch:
            return
        text = f"⚠️ هل أنت متأكد من حذف القناة <b>{ch.get('name')}</b>؟"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🗑️ نعم، احذف القناة", callback_data=f"chan_del_confirm:{cat_id}:{ch_id}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data=f"chan_view:{cat_id}:{ch_id}")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data.startswith("chan_del_confirm:"):
        _, cat_id, ch_id = data.split(":")
        if database.delete_channel(cat_id, ch_id):
            bot.answer_callback_query(call.id, "✅ تم حذف القناة بنجاح!")
            call.data = f"chans_list:{cat_id}"
            handle_callbacks(call)
        else:
            bot.answer_callback_query(call.id, "❌ فشل حذف القناة!", show_alert=True)
        return

    # 12. تعديل اسم قناة
    if data.startswith("chan_edit_name:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        user_states[user_id] = {"action": "waiting_chan_name", "cat_id": cat_id, "ch_id": ch_id}
        msg = bot.send_message(chat_id, f"✏️ اكتب الاسم الجديد لقناة <b>{ch.get('name')}</b>:")
        bot.register_next_step_handler(msg, step_update_chan_name)
        return

    # 13. تعديل رابط قناة
    if data.startswith("chan_edit_url:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        user_states[user_id] = {"action": "waiting_chan_url", "cat_id": cat_id, "ch_id": ch_id}
        msg = bot.send_message(chat_id, f"🔗 أرسل رابط البث الجديد لقناة <b>{ch.get('name')}</b>:")
        bot.register_next_step_handler(msg, step_update_chan_url)
        return

    # 14. تعديل صورة قناة
    if data.startswith("chan_edit_img:"):
        _, cat_id, ch_id = data.split(":")
        ch = database.get_channel(cat_id, ch_id)
        user_states[user_id] = {"action": "waiting_chan_img", "cat_id": cat_id, "ch_id": ch_id}
        msg = bot.send_message(chat_id, f"🖼️ أرسل رابط الشعار الجديد لقناة <b>{ch.get('name')}</b> أو أرسل صورة:")
        bot.register_next_step_handler(msg, step_update_chan_img)
        return

    # 15. إضافة قناة في قسم
    if data.startswith("chan_add:"):
        cat_id = data.split(":", 1)[1]
        cat = database.get_category(cat_id)
        user_states[user_id] = {"action": "adding_channel_step1", "cat_id": cat_id}
        msg = bot.send_message(chat_id, f"➕ <b>إضافة قناة جديدة إلى قسم {cat.get('name')}:</b>\n\nأرسل اسم القناة (مثال: beIN SPORTS 1 HD):")
        bot.register_next_step_handler(msg, step_add_channel_name)
        return

    # 16. مسار الربط السريع (Workflow: عند إرسال رابط)
    if data.startswith("link_cat_sel:"):
        cat_id = data.split(":", 1)[1]
        state = user_states.get(user_id, {})
        pending_url = state.get("pending_url")
        if not pending_url:
            bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط، أرسل الرابط مرة أخرى.", show_alert=True)
            return

        state["cat_id"] = cat_id
        cat = database.get_category(cat_id)
        channels = cat.get("channels", [])

        markup = types.InlineKeyboardMarkup(row_width=2)
        # زر إضافة كقناة جديدة بهذا الرابط
        markup.add(types.InlineKeyboardButton("➕ إضافة كقناة جديدة في هذا القسم", callback_data=f"link_chan_new:{cat_id}"))

        # قنوات القسم الحالية لاختيار أي منها لتحديث رابطها
        for ch in channels:
            markup.add(types.InlineKeyboardButton(f"📺 {ch.get('name')}", callback_data=f"link_chan_update:{cat_id}:{ch.get('id')}"))

        markup.add(types.InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="main_menu"))

        text = (
            f"📂 <b>تم اختيار قسم: {cat.get('name')}</b>\n"
            f"🔗 الرابط المراد حفظه:\n<code>{pending_url}</code>\n\n"
            "👇 <b>اختر الإجراء المطلوب:</b>\n"
            "• اضغط على <b>➕ إضافة كقناة جديدة</b> لإنشاء قناة جديدة بهذا الرابط.\n"
            "• أو اضغط على أي <b>قناة موجودة</b> لتحديث رابطها فورياً."
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data.startswith("link_chan_update:"):
        _, cat_id, ch_id = data.split(":")
        state = user_states.get(user_id, {})
        pending_url = state.get("pending_url")
        if not pending_url:
            bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط!", show_alert=True)
            return

        ch = database.get_channel(cat_id, ch_id)
        if not ch:
            return

        # تحديث الرابط فورياً
        database.update_channel(cat_id, ch_id, direct_url=pending_url)
        user_states.pop(user_id, None)

        bot.answer_callback_query(call.id, "✅ تم تحديث رابط القناة بنجاح!")
        text = (
            f"🎉 <b>تم تحديث رابط القناة بنجاح!</b>\n\n"
            f"• القناة: <b>{ch.get('name')}</b>\n"
            f"• رابط البث الجديد:\n<code>{pending_url}</code>\n\n"
            "التحديث نشط فوراً على تطبيق أحمد ال علي TV دون الحاجة لإعادة تشغيل!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📺 معاينة القناة", callback_data=f"chan_view:{cat_id}:{ch_id}"))
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data.startswith("link_chan_new:"):
        cat_id = data.split(":", 1)[1]
        state = user_states.get(user_id, {})
        pending_url = state.get("pending_url")
        if not pending_url:
            bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط!", show_alert=True)
            return

        cat = database.get_category(cat_id)
        user_states[user_id]["action"] = "waiting_link_new_chan_name"
        user_states[user_id]["cat_id"] = cat_id

        msg = bot.send_message(chat_id, f"➕ اكتب اسم القناة الجديدة التي سيتم إنشاؤها في قسم <b>{cat.get('name')}</b> بالرابط:\n<code>{pending_url}</code>")
        bot.register_next_step_handler(msg, step_link_new_chan_name)
        return

    # 17. استيراد ملف M3U إلى قسم
    if data.startswith("m3u_cat_import:"):
        cat_id = data.split(":", 1)[1]
        state = user_states.get(user_id, {})
        channels = state.get("channels", [])
        if not channels:
            bot.answer_callback_query(call.id, "⚠️ لا توجد قنوات محفوظة للاستيراد!", show_alert=True)
            return

        cat = database.get_category(cat_id)
        bot.answer_callback_query(call.id, "⏳ جاري استيراد القنوات...")
        added_count = database.import_m3u_channels_to_category(cat_id, channels)
        user_states.pop(user_id, None)

        text = (
            f"🎉 <b>تم استيراد القنوات بنجاح!</b>\n\n"
            f"• القسم: <b>{cat.get('name')}</b>\n"
            f"• عدد القنوات المضافة: <b>{added_count}</b> قناة\n\n"
            "جميع القنوات متاحة الآن في التطبيق تلقائياً."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📺 عرض قنوات القسم", callback_data=f"chans_list:{cat_id}"))
        markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 18. قائمة النسخ الاحتياطي
    if data == "backup_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        b_dl = types.InlineKeyboardButton("📥 تنزيل نسخة احتياطية (JSON)", callback_data="backup_download")
        b_def = types.InlineKeyboardButton("🔄 استعادة القنوات الافتراضية", callback_data="backup_restore_defaults_ask")
        b_back = types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu")
        markup.add(b_dl)
        markup.add(b_def)
        markup.add(b_back)

        text = (
            "💾 <b>نظام النسخ الاحتياطي والاستعادة:</b>\n\n"
            "• يمكنك تنزيل ملف قاعدة البيانات الكامل (data.json) بنقرة زر.\n"
            "• لاستعادة أي نسخة: فقط أرسل ملف <code>.json</code> للبوت وسيتولى استعادته تلقائياً بعد فحص أمانه.\n"
            "• يمكنك أيضاً إعادة ضبط التطبيق واستعادة البيانات الافتراضية الرسمية."
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data == "backup_download":
        bot.answer_callback_query(call.id, "⏳ جاري إرسال النسخة الاحتياطية...")
        backup_path = database.create_backup()
        if backup_path and os.path.exists(backup_path):
            with open(backup_path, "rb") as f:
                bot.send_document(chat_id, f, caption=f"💾 نسخة احتياطية لتطبيق أحمد ال علي TV\nتاريخ: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return

    if data == "backup_restore_defaults_ask":
        text = (
            "⚠️ <b>تحذير: استعادة البيانات الافتراضية!</b>\n\n"
            "سيتم استرجاع جميع الأقسام والقنوات الأصلية (beIN, SSC, STARZPLAY, أبوظبي, إلخ) وحذف أي تعديلات مخصصة غير محفوظة في نسخة سابقة.\n"
            "هل أنت متأكد من المتابعة؟"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔄 نعم، استعد الافتراضية", callback_data="backup_restore_defaults_confirm"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="backup_menu")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data == "backup_restore_defaults_confirm":
        database.create_backup()
        database.reset_to_default_data()
        bot.answer_callback_query(call.id, "✅ تمت استعادة البيانات الافتراضية بنجاح!")
        call.data = "main_menu"
        handle_callbacks(call)
        return

    # 19. معلومات خادم الـ API والربط بالتطبيق
    if data == "api_info":
        stats = database.get_stats()
        host = API_HOST if API_HOST != "0.0.0.0" else "IP_الخادم_أو_الجهاز"
        api_base = PUBLIC_API_URL or f"http://{host}:{API_PORT}"

        text = (
            "⚙️ <b>إعدادات خادم الـ API والربط بتطبيق أحمد ال علي TV:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 <b>رابط مزامنة التطبيق (Data API):</b>\n"
            f"<code>{api_base}/api/data</code>\n\n"
            f"📁 <b>رابط الأقسام فقط:</b>\n"
            f"<code>{api_base}/api/categories</code>\n\n"
            f"🤖 <b>يوزرنيم البوت المربوط:</b>\n"
            f"@{BOT_USERNAME}\n\n"
            "💡 <b>كيف يتم الربط داخل التطبيق؟</b>\n"
            "1. التطبيق مبرمج لجلب وتحديث القنوات تلقائياً من خادم الـ API أعلاه.\n"
            "2. عند الضغط على زر <b>القنوات</b> داخل التطبيق، أو عبر زر <b>إعدادات السيرفر</b> في الشاشة، يمكنك إدخال هذا الرابط ويتم حفظه تلقائياً.\n"
            "3. أي تغيير تجريه هنا في البوت ينعكس فوراً على هواتف جميع مستخدمي التطبيق!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # 20. إدارة المشرفين (Super Admin فقط)
    if data == "admins_menu":
        if not database.is_super_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ هذا القسم مخصص لمالك التطبيق فقط!", show_alert=True)
            return

        admins = database.load_admins()
        text = "👥 <b>قائمة المشرفين المعتمدين:</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=2)

        for a in admins:
            role = "👑 مالك أساسي" if a.get("is_super_admin") else "👮 مشرف"
            text += f"• {role}: <b>{a.get('username')}</b> (ID: <code>{a.get('user_id')}</code>)\n"
            if not a.get("is_super_admin"):
                markup.add(types.InlineKeyboardButton(f"🗑️ حذف {a.get('username')}", callback_data=f"admin_del:{a.get('user_id')}"))

        markup.add(types.InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="main_menu"))

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data == "admin_add":
        if not database.is_super_admin(user_id):
            return
        user_states[user_id] = {"action": "waiting_admin_id"}
        msg = bot.send_message(chat_id, "➕ <b>إضافة مشرف جديد:</b>\n\nأرسل معرف التيليجرام الخاص بالمشرف (Telegram ID - أرقام فقط):")
        bot.register_next_step_handler(msg, step_add_admin_id)
        return

    if data.startswith("admin_del:"):
        if not database.is_super_admin(user_id):
            return
        target_id = int(data.split(":", 1)[1])
        if database.remove_admin(target_id):
            bot.answer_callback_query(call.id, "✅ تم حذف المشرف بنجاح!")
            call.data = "admins_menu"
            handle_callbacks(call)
        else:
            bot.answer_callback_query(call.id, "❌ تعذر حذف المشرف!", show_alert=True)
        return

# ==============================================================================
# دوال استكمال الخطوات (Step Handlers)
# ==============================================================================

def step_update_cat_name(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    new_name = message.text.strip() if message.text else ""
    if new_name and cat_id:
        database.update_category(cat_id, name=new_name)
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, f"✅ تم تحديث اسم القسم إلى: <b>{new_name}</b>", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "⚠️ لم يتم إدخال اسم صالح.")

def step_update_cat_image(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    img_url = ""

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    elif message.text:
        img_url = message.text.strip()

    if img_url and cat_id:
        database.update_category(cat_id, image=img_url)
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "✅ تم تحديث صورة/شعار القسم بنجاح!", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "⚠️ لم يتم استلام صورة أو رابط صالح.")

def step_add_cat_name(message):
    user_id = message.from_user.id
    name = message.text.strip() if message.text else ""
    if not name:
        bot.send_message(message.chat.id, "⚠️ الاسم لا يمكن أن يكون فارغاً.")
        return
    user_states[user_id] = {"action": "waiting_new_cat_img", "name": name}
    msg = bot.send_message(message.chat.id, f"🖼️ الآن أرسل رابط شعار القسم <b>{name}</b> (أو أرسل كلمة 'افتراضي' لاستخدام الشعار التلقائي):")
    bot.register_next_step_handler(msg, step_add_cat_img)

def step_add_cat_img(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    name = state.get("name")
    img_url = "https://f.top4top.io/p_3804lcnvq1.png"

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    elif message.text and message.text.strip() != "افتراضي":
        img_url = message.text.strip()

    new_cat = database.add_category(name, img_url)
    user_states.pop(user_id, None)

    if new_cat:
        bot.send_message(message.chat.id, f"🎉 <b>تم إنشاء القسم بنجاح!</b>\n• الاسم: <b>{name}</b>\n• المعرف: <code>{new_cat['id']}</code>", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إنشاء القسم.")

def step_update_chan_name(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    ch_id = state.get("ch_id")
    name = message.text.strip() if message.text else ""
    if name and cat_id and ch_id:
        database.update_channel(cat_id, ch_id, name=name)
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, f"✅ تم تحديث اسم القناة إلى: <b>{name}</b>", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "⚠️ اسم غير صالح.")

def step_update_chan_url(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    ch_id = state.get("ch_id")
    url = message.text.strip() if message.text else ""
    if url and cat_id and ch_id:
        database.update_channel(cat_id, ch_id, direct_url=url)
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "✅ تم تحديث رابط بث القناة بنجاح وهو شغال الآن في التطبيق!", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "⚠️ رابط غير صالح.")

def step_update_chan_img(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    ch_id = state.get("ch_id")
    img_url = ""
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    elif message.text:
        img_url = message.text.strip()

    if img_url and cat_id and ch_id:
        database.update_channel(cat_id, ch_id, image=img_url)
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "✅ تم تحديث صورة القناة بنجاح!", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "⚠️ صورة غير صالحة.")

def step_add_channel_name(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    name = message.text.strip() if message.text else ""
    if not name:
        bot.send_message(message.chat.id, "⚠️ الاسم لا يمكن أن يكون فارغاً.")
        return
    user_states[user_id]["name"] = name
    msg = bot.send_message(message.chat.id, f"🔗 أرسل الآن رابط البث المباشر لقناة <b>{name}</b> (M3U8 أو TS أو مباشر):")
    bot.register_next_step_handler(msg, step_add_channel_url)

def step_add_channel_url(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    url = message.text.strip() if message.text else ""
    if not url:
        bot.send_message(message.chat.id, "⚠️ الرابط مطلوب.")
        return
    user_states[user_id]["direct_url"] = url
    msg = bot.send_message(message.chat.id, "🖼️ أرسل رابط صورة/شعار القناة (أو أرسل 'تلقائي' لاستخدام شعار القسم):")
    bot.register_next_step_handler(msg, step_add_channel_final)

def step_add_channel_final(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    name = state.get("name")
    url = state.get("direct_url")
    cat = database.get_category(cat_id)

    img_url = cat.get("image", "")
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    elif message.text and message.text.strip() != "تلقائي":
        img_url = message.text.strip()

    new_ch = database.add_channel(cat_id, name, url, img_url)
    user_states.pop(user_id, None)

    if new_ch:
        bot.send_message(message.chat.id, f"🎉 <b>تمت إضافة القناة بنجاح!</b>\n• الاسم: <b>{name}</b>\n• القسم: <b>{cat.get('name')}</b>\n• الرابط:\n<code>{url}</code>", reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id)))
    else:
        bot.send_message(message.chat.id, "❌ فشل في إضافة القناة.")

def step_link_new_chan_name(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    cat_id = state.get("cat_id")
    pending_url = state.get("pending_url")
    name = message.text.strip() if message.text else ""

    if not name or not cat_id or not pending_url:
        bot.send_message(message.chat.id, "⚠️ بيانات غير مكتملة.")
        return

    cat = database.get_category(cat_id)
    new_ch = database.add_channel(cat_id, name, pending_url, cat.get("image", ""))
    user_states.pop(user_id, None)

    if new_ch:
        bot.send_message(
            message.chat.id,
            f"🎉 <b>تم إنشاء القناة وربط البث بنجاح!</b>\n\n"
            f"• القناة: <b>{name}</b>\n"
            f"• القسم: <b>{cat.get('name')}</b>\n"
            f"• الرابط:\n<code>{pending_url}</code>\n\n"
            "القناة متاحة الآن داخل تطبيق أحمد ال علي TV!",
            reply_markup=get_main_menu_keyboard(database.is_super_admin(user_id))
        )
    else:
        bot.send_message(message.chat.id, "❌ فشل في إنشاء القناة.")

def step_add_admin_id(message):
    user_id = message.from_user.id
    if not database.is_super_admin(user_id):
        return
    raw = message.text.strip() if message.text else ""
    try:
        new_admin_id = int(raw)
        added = database.add_admin(new_admin_id, username=f"Admin_{new_admin_id}")
        if added:
            bot.send_message(message.chat.id, f"✅ تم تعيين المستخدم (ID: <code>{new_admin_id}</code>) كمشرف معتمد بنجاح!", reply_markup=get_main_menu_keyboard(True))
        else:
            bot.send_message(message.chat.id, "❌ فشل في إضافة المشرف.")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ معرف غير صالح، يرجى إدخال أرقام فقط.")

def start_bot():
    """تشغيل البوت في وضع الاستماع المستمر"""
    if not BOT_TOKEN or ":" not in BOT_TOKEN or active_token == DUMMY_TOKEN:
        print("❌ لم يتم تحديد BOT_TOKEN صالح في ملف .env!")
        print("💡 احصل على التوكن من @BotFather وضعه في .env كالتالي: BOT_TOKEN=123456:ABC-...")
        return
    print(f"🤖 Bot @{BOT_USERNAME} is running and polling...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    start_bot()

