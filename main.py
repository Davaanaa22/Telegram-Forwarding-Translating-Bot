import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Read variables from .env
TOKEN = os.getenv("API")
SOURCE_CHANNEL = int(os.getenv("TEST2"))
DESTINATION_CHANNEL = int(os.getenv("TEST"))

# Translator instance
translator = GoogleTranslator(source="en", target="mn")

# Forex terms and their English replacements
forex_terms = {
    "АЛТ": "GOLD",
    "ЗАРНА": "SELL",
    "зарна": "SELL",
    "ХУДАЛДАА": "BUY",
    "ХУДАЛДАН АВАХ": "BUY",
    "ХУДАЛДАН АВАРАЙ": "BUY",
    "ХУДАЛДАН АВНА": "BUY",
    "Алдагдлаа зогсооно": "Stop Loss",
    "Алдагдлыг зогсоох": "Stop Loss",
    "Ашиг аваарай": "Take Profit",
    "АШИГ АВАХ": "Take Profit",
    "дахин": "X",
    "АШИГ АВ": "Take Profit",
    "Ашиг авна": "Take Profit",
    "Дээрх оруулна уу": "Арилжаанд орох ханш ",
    "хамгийн их утга нь ": "Арилжаанд орох хамгийн дээд ханш ",
    "ХУДАЛДАН АВААР АВЧ Ашиг": "Take Profit",
    "PIPS": "PIPS",
    "EURNZD": "EURNZD",
    "GBPCAD": "GBPCAD",
    "EURJPY": "EURJPY",
}

# Reverse forex terms for replacement in text
forex_terms_reverse = {v: k for k, v in forex_terms.items()}


def custom_translate(text: str) -> str:
    """
    Translate the entire text to Mongolian.
    """
    translated_text = translator.translate(text)
    return translated_text


def replace_forex_terms(text: str) -> str:
    """
    Replace the translated forex terms back to English.
    """
    # Iterate through forex terms and replace both in Mongolian and English context
    for term_mn, term_en in forex_terms.items():
        text = re.sub(rf"\b{re.escape(term_mn)}\b", term_en, text)
    return text


def process_text(message_text: str) -> str:
    """
    Process the message text to filter out unwanted content and add promotional text.
    """
    # Filter out promotional messages
    if re.search(
        r"\b(Ad|offer|altcoin|apology|sorry|support|market)\b",
        message_text,
        re.IGNORECASE,
    ):
        logger.info("Skipping promotional message.")
        return None

    # Replace green hearts with dollar emojis (if needed)
    filtered_text = message_text.replace("💚", "💵")

    # Remove content below the horizontal line
    parts = re.split(r"[-—_]{3,}", filtered_text)
    filtered_text = parts[0].strip()

    # Remove content after fire emoji (if needed)
    parts = filtered_text.split("🔥")
    filtered_text = parts[0].strip()

    # Remove guide and weblink
    filtered_text = re.sub(
        r"📚Guide:.*$", "", filtered_text, flags=re.MULTILINE
    ).strip()

    # Remove everything after the ⚠️ emoji (including the emoji itself)
    filtered_text = re.sub(r"⚠️.*$", "", filtered_text, flags=re.MULTILINE).strip()

    # **Remove everything after the 👋 emoji (including the emoji itself)**
    filtered_text = re.sub(r"👋.*$", "", filtered_text, flags=re.MULTILINE).strip()

    # Remove any text that contains 'WOLFXSIGNALS.COM'
    filtered_text = re.sub(r"(?i).*WOLFXSIGNALS\.COM.*", "", filtered_text).strip()

    # **Remove any line that contains '@WOLFX_SIGNALS'**
    filtered_text = re.sub(r"(?i)^.*@WOLFX_SIGNALS.*\n?", "", filtered_text)

    # Remove trailing or unnecessary whitespace
    filtered_text = filtered_text.strip()

    return filtered_text if filtered_text else None


def is_signal_message(text: str) -> bool:
    """
    Determine if a message is a signal message based on its format.
    """
    return bool(re.search(r"\b(SL|TP\d+)\b", text))


# Async function to handle translation and copying
async def copy_and_translate_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    try:
        if update.channel_post and update.channel_post.chat_id == SOURCE_CHANNEL:
            original_message = update.channel_post

            if original_message.text:
                processed_text = process_text(original_message.text)
                if processed_text:
                    translated_text = custom_translate(processed_text)
                    final_text = replace_forex_terms(translated_text)

                    # Check if the message is a signal message
                    if is_signal_message(final_text):
                        final_text += " \n\n ❗️Арилжаанд орох хамгийн дээд ханшнаас дээгүүр орсон тохиолдолд энэхүү арилжаа нь манай сувгийн signal-тай нийцэхгүй."

                    # Append the promotional text
                    final_text += " \n\n 💸💸💸 Plus-Mongolia-Signal 💰💰💰"

                    await context.bot.send_message(
                        chat_id=DESTINATION_CHANNEL, text=final_text
                    )
            elif original_message.caption and original_message.photo:
                processed_caption = process_text(original_message.caption)
                if processed_caption:
                    translated_caption = custom_translate(processed_caption)
                    final_caption = replace_forex_terms(translated_caption)

                    # Check if the message is a signal message
                    if is_signal_message(final_caption):
                        final_caption += " \n\n ❗️Арилжаанд орох хамгийн дээд ханшнаас дээгүүр орсон тохиолдолд энэхүү арилжаа нь манай сувгийн signal-тай нийцэхгүй."

                    # Append the promotional text
                    final_caption += " \n\n 💸💸💸 Plus-Mongolia-Signal 💰💰💰"

                    await context.bot.send_message(
                        chat_id=DESTINATION_CHANNEL, text=final_caption
                    )
            logger.info("Message processed, translated, and copied successfully.")
    except Exception as e:
        logger.error(f"Error translating or copying message: {e}")


def main():
    # Create the bot application
    application = Application.builder().token(TOKEN).build()

    # Add a message handler to handle posts in the source channel
    application.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST, copy_and_translate_message)
    )

    # Run the bot
    logger.info("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
