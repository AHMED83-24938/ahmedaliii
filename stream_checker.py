import re
import time
import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

def detect_link_type(url, content_type="", sample_text=""):
    """
    تحديد نوع الرابط:
    - m3u8: بث مباشر بتقنية HLS
    - m3u: قائمة تشغيل تحوي عدة قنوات
    - js: سكربت جافاسكربت أو محلل بث (Resolver)
    - direct: رابط بث وسائط مباشر (mp4, ts, etc.)
    - unknown: رابط عام
    """
    url_lower = url.lower()
    ct_lower = (content_type or "").lower()
    sample = (sample_text or "").strip()

    if sample.startswith("#EXTM3U") or ".m3u" in url_lower:
        # هل هو ملف قائمة كاملة أم بث مفرد؟
        if sample.count("#EXTINF:") > 1:
            return "m3u"
        if ".m3u8" in url_lower or "mpegurl" in ct_lower:
            return "m3u8"
        return "m3u"

    if ".m3u8" in url_lower or "mpegurl" in ct_lower:
        return "m3u8"

    if ".js" in url_lower or "javascript" in ct_lower:
        return "js"

    if any(ext in url_lower for ext in [".ts", ".mp4", ".mkv", ".flv", ".mov", ".avi"]):
        return "direct"

    return "unknown"

def check_stream_url(url, timeout=6):
    """
    فحص صحة واستجابة رابط البث بدقة:
    - التحقق من كود الاستجابة (HTTP Status Code)
    - حساب سرعة الاستجابة بالمللي ثانية
    - فحص نوع المحتوى (Content-Type)
    - كشف الروابط المشفرة أو السكربتات
    """
    start_time = time.time()
    result = {
        "url": url,
        "is_valid": False,
        "status_code": 0,
        "type": "unknown",
        "latency_ms": 0,
        "content_type": "",
        "extracted_streams": [],
        "message": ""
    }

    try:
        # إرسال طلب خفيف (stream=True لتحميل أول جزء فقط)
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, stream=True, allow_redirects=True)
        latency = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency
        result["status_code"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")

        # قراءة أول 2048 بايت لمعاينة المحتوى
        sample_bytes = b""
        for chunk in resp.iter_content(chunk_size=2048):
            sample_bytes = chunk
            break
        resp.close()

        sample_text = ""
        try:
            sample_text = sample_bytes.decode("utf-8", errors="ignore")
        except Exception:
            pass

        link_type = detect_link_type(url, result["content_type"], sample_text)
        result["type"] = link_type

        # إذا كان الرابط جافاسكربت، نبحث عن أي روابط m3u8 مخفية بداخله
        if link_type == "js" or "javascript" in result["content_type"].lower():
            extracted = re.findall(r'https?://[^\s\'"<>]+(?:\.m3u8|\.ts|\.mp4)[^\s\'"<>]*', sample_text)
            if extracted:
                result["extracted_streams"] = list(set(extracted))

        if resp.status_code in [200, 206, 301, 302]:
            result["is_valid"] = True
            if link_type == "m3u8":
                result["message"] = f"✅ بث HLS M3U8 سليم وشغال (الاستجابة: {latency}ms)"
            elif link_type == "m3u":
                result["message"] = f"📑 قائمة تشغيل M3U صالحة (الاستجابة: {latency}ms)"
            elif link_type == "js":
                if result["extracted_streams"]:
                    result["message"] = f"⚡ سكربت JS مباشر تم استخراج بث منه (الاستجابة: {latency}ms)"
                else:
                    result["message"] = f"⚡ رابط JS / Resolver مستجيب (الاستجابة: {latency}ms)"
            else:
                result["message"] = f"✅ رابط البث متصل وشغال (الاستجابة: {latency}ms)"
        else:
            result["is_valid"] = False
            result["message"] = f"⚠️ الخادم أرجع رمز استجابة ({resp.status_code})"

    except requests.exceptions.Timeout:
        result["message"] = "⏱️ انتهت مهلة الاتصال بالرابط (Timeout)"
    except requests.exceptions.ConnectionError:
        result["message"] = "❌ تعذر الاتصال بالخادم (Connection Error)"
    except Exception as e:
        result["message"] = f"❌ خطأ في فحص الرابط: {str(e)[:100]}"

    return result

def parse_m3u_text(content):
    """
    تحليل نص ملف أو رابط M3U واستخراج جميع القنوات:
    - اسم القناة
    - رابط البث المباشر
    - صورة/شعار القناة (tvg-logo)
    - تصنيف القناة (group-title)
    """
    channels = []
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    current_channel = None

    for line in lines:
        if line.startswith("#EXTINF:"):
            # استخراج بيانات القناة
            name = ""
            logo = ""
            group = ""

            # البحث عن tvg-logo
            logo_match = re.search(r'tvg-logo=["\']([^"\']+)["\']', line)
            if logo_match:
                logo = logo_match.group(1).strip()

            # البحث عن group-title
            group_match = re.search(r'group-title=["\']([^"\']+)["\']', line)
            if group_match:
                group = group_match.group(1).strip()

            # الاسم يقع عادة بعد آخر فاصلة في السطر
            parts = line.split(",", 1)
            if len(parts) > 1:
                name = parts[1].strip()
            else:
                name = "قناة بدون اسم"

            current_channel = {
                "name": name,
                "image": logo,
                "group": group,
                "direct_url": ""
            }
        elif line.startswith("http://") or line.startswith("https://") or line.startswith("rtmp://"):
            if current_channel:
                current_channel["direct_url"] = line.strip()
                channels.append(current_channel)
                current_channel = None

    return channels

def download_and_parse_m3u(url, timeout=10):
    """تحميل قائمة M3U من رابط خارجي وتحليلها"""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return parse_m3u_text(resp.text)
    except Exception as e:
        print(f"Error downloading M3U: {e}")
    return []
