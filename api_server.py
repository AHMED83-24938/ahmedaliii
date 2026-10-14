import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import database
from config import API_HOST, API_PORT

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class TVApiHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # تسجيل خفيف لعدم إغراق شاشة الطرفية
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.end_headers()
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.wfile.write(json_bytes)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # 1. فحص صحة الخادم (Health Check)
        if path == "" or path == "/api" or path == "/api/status" or path == "/api/health":
            stats = database.get_stats()
            self.send_json(200, {
                "status": "online",
                "service": "أحمد ال علي TV - Live API",
                "version": "2.0.0",
                "stats": stats
            })
            return

        # 2. جلب جميع الأقسام فقط (Categories)
        if path == "/api/categories":
            cats = database.get_categories()
            self.send_json(200, cats)
            return

        # 3. جلب جميع البيانات مجمعة (الأقسام وقنواتها دفعة واحدة لمزامنة التطبيق)
        if path == "/api/data" or path == "/api/all":
            all_data = database.load_data()
            self.send_json(200, all_data)
            return

        # 4. جلب قنوات قسم معين
        # مسار: /api/channels?category_id=1 أو /api/categories/<id>/channels
        if path == "/api/channels":
            cat_id = query.get("category_id", [""])[0] or query.get("cat_id", [""])[0]
            if not cat_id:
                self.send_json(400, {"error": "Missing category_id parameter"})
                return
            channels = database.get_channels(cat_id)
            self.send_json(200, channels)
            return

        if path.startswith("/api/categories/") and path.endswith("/channels"):
            parts = path.split("/")
            if len(parts) >= 4:
                cat_id = parts[3]
                channels = database.get_channels(cat_id)
                self.send_json(200, channels)
                return

        # 5. البحث في القنوات
        if path == "/api/search":
            q = query.get("q", [""])[0]
            if not q:
                self.send_json(200, [])
                return
            results = database.search_channels_global(q)
            self.send_json(200, results)
            return

        # مسار غير موجود
        self.send_json(404, {"error": "Endpoint not found", "path": path})

def start_api_server(host=API_HOST, port=API_PORT):
    """تشغيل خادم الـ API"""
    server_address = (host, port)
    server = ThreadedHTTPServer(server_address, TVApiHandler)
    print(f"🚀 TV API Server running at http://{host}:{port}/")
    print(f"📡 Sync Endpoint for App: http://{host}:{port}/api/data")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    start_api_server()
