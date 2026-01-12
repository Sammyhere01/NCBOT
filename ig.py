# ==================================
#        Sammy - Telegram IG Bot
# ==================================

import json
import os
import time
import subprocess
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN"

SESSIONID = 1
users_delay = {}  # user_id -> delay seconds

# ---------------- Utils ----------------

def user_file(user_id):
    return f"user_{user_id}.json"

def load_user(user_id):
    if os.path.exists(user_file(user_id)):
        return json.load(open(user_file(user_id)))
    return {"accounts": [], "default": None}

def save_user(user_id, data):
    with open(user_file(user_id), "w") as f:
        json.dump(data, f)

def storage_from_sessionid(sessionid):
    return {
        "cookies": [
            {
                "name": "sessionid",
                "value": sessionid,
                "domain": ".instagram.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
                "expires": int(time.time()) + 365*24*3600
            }
        ],
        "origins": [{"origin": "https://www.instagram.com", "localStorage": []}]
    }

# ---------------- Commands ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *Sammy IG Bot* 🔥\n\n"
        "/sessionid – Login using cookies\n"
        "/delay <sec> – Set rename delay\n"
        "/attack – Start GC rename",
        parse_mode="Markdown"
    )

# ---- Delay ----
async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /delay 5")
        return
    users_delay[user_id] = int(context.args[0])
    await update.message.reply_text(
        f"⏱ Delay set to {users_delay[user_id]} seconds"
    )

# ---- SessionID Login ----
async def sessionid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Send your Instagram sessionid:")
    return SESSIONID

async def sessionid_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessionid = update.message.text.strip()

    state = storage_from_sessionid(sessionid)
    data = load_user(user_id)

    data["accounts"].append({
        "ig_username": f"session_{user_id}",
        "storage_state": state
    })
    data["default"] = len(data["accounts"]) - 1

    save_user(user_id, data)

    await update.message.reply_text("✅ SessionID login saved (Sammy)")
    return ConversationHandler.END

# ---- Attack ----
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_user(user_id)

    if data["default"] is None:
        await update.message.reply_text("❌ Login first using /sessionid")
        return

    await update.message.reply_text(
        "📝 Send message in this format:\n\n"
        "GC_URL\n"
        "name1,name2,name3"
    )
    context.user_data["awaiting"] = True

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting"):
        return

    user_id = update.effective_user.id
    lines = update.message.text.strip().split("\n", 1)

    if len(lines) != 2:
        await update.message.reply_text("❌ Invalid format")
        return

    thread_url = lines[0].strip()
    names = lines[1].strip()

    data = load_user(user_id)
    acc = data["accounts"][data["default"]]

    state_file = f"state_{user_id}.json"
    with open(state_file, "w") as f:
        json.dump(acc["storage_state"], f)

    delay = users_delay.get(user_id, 3)

    cmd = [
        "python3", "ig.py",
        "--thread-url", thread_url,
        "--names", names,
        "--delay", str(delay),
        "--storage-state", state_file
    ]

    subprocess.Popen(cmd)

    await update.message.reply_text(
        "💥 GC rename started by *Sammy* 💥",
        parse_mode="Markdown"
    )

    context.user_data.clear()

# ---------------- Main ----------------

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("delay", delay_cmd))
    app.add_handler(CommandHandler("attack", attack))

    conv = ConversationHandler(
        entry_points=[CommandHandler("sessionid", sessionid_start)],
        states={
            SESSIONID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sessionid_save)
            ]
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("🔥 Sammy Bot Running 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
