import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== خواندن توکن از Secrets گیت‌هاب ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# =================================================

# فقط به کاربر مجاز اجازه بده ازش استفاده کنه
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", 0))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوش‌آمدگویی"""
    await update.message.reply_text(
        "سلام! من یه ربات دانلودر ساده هستم.\n"
        "کافیه یه لینک مستقیم (مثل لینک یک فایل) برام بفرستی تا دانلودش کنم و برات بفرستم.\n"
        "⚠️ فقط فایل‌های زیر ۵۰ مگابایت قابل ارسال هستن."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌ها: بررسی و دانلود لینک"""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("⛔ دسترسی محدود.")
        return

    text = update.message.text
    # جستجوی لینک در متن (حتی اگه قبلش /download نزده باشه)
    url_match = re.search(r'(https?://[^\s]+)', text)
    if not url_match:
        await update.message.reply_text("❌ لینکی پیدا نشد. لطفاً یک لینک مستقیم بفرست.")
        return

    url = url_match.group(1)
    await update.message.reply_text("⬇️ در حال دانلود فایل... لطفاً صبر کن.")

    try:
        # دانلود فایل با stream (برای جلوگیری از مصرف زیاد حافظه)
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        # استخراج اسم فایل از لینک
        filename = os.path.basename(url.split("?")[0])
        if not filename:
            filename = "downloaded_file"

        # بررسی حجم فایل (از هدر Content-Length که اگه سرور بده)
        file_size = int(response.headers.get('content-length', 0))
        if file_size > 50 * 1024 * 1024:
            await update.message.reply_text(f"⚠️ فایل بزرگتر از ۵۰ مگابایت ({file_size / (1024*1024):.1f} MB) هست. تلگرام اجازه ارسال فایل با این حجم رو نمیده.\n🔗 لینک: {url}")
            return

        # ذخیره موقت فایل
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # ارسال فایل به عنوان سند
        with open(temp_path, 'rb') as f:
            await update.message.reply_document(document=f, filename=filename, caption=f"📄 {filename}")

        # پاک کردن فایل موقت
        os.remove(temp_path)
        await update.message.reply_text("✅ دانلود و ارسال با موفقیت انجام شد.")

    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ زمان دانلود به پایان رسید. لینک کند است.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ ربات دانلودر روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
