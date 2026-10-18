
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    ContextTypes,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "8879570673"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "REO Premium Guard is running."
    )


async def check_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    request = update.chat_join_request
    user = request.from_user

    username = f"@{user.username}" if user.username else "None"

    if user.is_premium is True:
        try:
            await request.decline()
            status = "PREMIUM"
            action = "Request declined."
        except Exception as error:
            status = "PREMIUM"
            action = f"Decline failed: {error}"
    elif user.is_premium is False:
        status = "NON-PREMIUM"
        action = "Request left pending."
    else:
        status = "UNKNOWN"
        action = "Request left pending."

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=(
            "REO PREMIUM GUARD\n"
            f"Name: {user.full_name}\n"
            f"Username: {username}\n"
            f"User ID: {user.id}\n"
            f"Premium Status: {status}\n"
            f"Action: {action}"
        ),
    )


def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(check_request))
    app.run_polling(
        allowed_updates=["message", "chat_join_request"]
    )


if __name__ == "__main__":
    main()
