
import os
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("reo_guard")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "8879570673"))

# Limit simultaneous Telegram API operations.
api_semaphore = asyncio.Semaphore(8)

# Prevent the same request being processed twice concurrently.
in_progress = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "REO Premium Guard is running."
    )


async def check_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    request = update.chat_join_request
    if request is None:
        return

    key = (request.chat.id, request.from_user.id)

    if key in in_progress:
        logger.warning("Duplicate in-progress request: %s", key)
        return

    in_progress.add(key)
    user = request.from_user

    username = f"@{user.username}" if user.username else "None"
    status = "UNKNOWN"
    action = "Request left pending."

    try:
        async with api_semaphore:
            if user.is_premium is True:
                status = "PREMIUM"
                try:
                    await request.decline()
                    action = "Request declined."
                except Exception:
                    action = "Decline failed; check logs."
                    logger.exception(
                        "Could not decline request for user %s",
                        user.id,
                    )

            elif user.is_premium is False:
                status = "NON-PREMIUM"

            # Send a report for every received request.
            try:
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
                logger.info(
                    "Report sent: user=%s status=%s action=%s",
                    user.id, status, action,
                )
            except Exception:
                logger.exception(
                    "Could not send report for user %s",
                    user.id,
                )

    except Exception:
        logger.exception("Request processing failed for user %s", user.id)

    finally:
        in_progress.discard(key)


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Unhandled bot error",
        exc_info=context.error,
    )


def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing.")

    app = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(16)
        .connection_pool_size(20)
        .pool_timeout(10)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(check_request))
    app.add_error_handler(error_handler)

    logger.info("REO Premium Guard starting")
    app.run_polling(
        allowed_updates=["message", "chat_join_request"]
    )


if __name__ == "__main__":
    main()
