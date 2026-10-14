#!/bin/bash
# سكربت تشغيل خادم وبوت تطبيق أحمد ال علي TV

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "🚀 تشغيل نظام إدارة تطبيق أحمد ال علي TV..."
echo "=========================================================="

# التأكد من الحزم المطلوبة
python3 -m pip install -r requirements.txt --quiet 2>/dev/null

# دالة للتنظيف عند الإيقاف
cleanup() {
    echo ""
    echo "🛑 إيقاف النظام..."
    kill $SERVER_PID $BOT_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# تشغيل الخادم في الخلفية
echo "▶️  تشغيل الخادم (main.py)..."
python3 main.py &
SERVER_PID=$!

# انتظار قصير ليفتح الخادم المنفذ
sleep 2

# تشغيل البوت في الخلفية
echo "▶️  تشغيل البوت (main2.py)..."
python3 main2.py &
BOT_PID=$!

echo "✅ تم التشغيل. الخادم PID=$SERVER_PID | البوت PID=$BOT_PID"
echo "   اضغط Ctrl+C للإيقاف."

# انتظار انتهاء العمليتين
wait
