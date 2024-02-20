import logging
from datetime import datetime
from os import path as ospath
from colab_leecher import colab_bot
from colab_leecher.utility.variables import Transfer, Paths, Messages
from colab_leecher.utility.helper import speedETA, sizeUnit, status_bar

async def media_identifier(link):
    parts = link.split("/")
    message_id, message = parts[-1], None
    msg_chat_id = "-100" + parts[4]
    message_id, msg_chat_id = int(message_id), int(msg_chat_id)
    try:
        message = await colab_bot.get_messages(msg_chat_id, message_id)
    except Exception as e:
        logging.error(f"Error getting messages: {e}")
        return None, None

    media_types = ["document", "photo", "video", "audio", "voice", "video_note", "sticker", "animation"]
    media = next((getattr(message, media_type) for media_type in media_types if hasattr(message, media_type)), None)
    if media is None:
        logging.error("No media found in the message.")
    return media, message

async def download_progress(current, total, start_time):
    speed_string, eta, percentage = speedETA(start_time, current, total)
    await status_bar(
        down_msg=Messages.status_head,
        speed=speed_string,
        percentage=percentage,
        eta=eta,
        done=sizeUnit(sum(Transfer.down_bytes) + current),
        left=sizeUnit(Transfer.total_down_size),
        engine="Pyrogram 💥",
    )

async def telegram_download(link, num):
    global start_time
    media, message = await media_identifier(link)
    if media is None:
        logging.error("No media found. Download aborted.")
        return

    name = media.file_name if hasattr(media, "file_name") else "Unknown"
    Messages.status_head = f"<b>📥 DOWNLOADING FROM » </b><i>🔗Link {str(num).zfill(2)}</i>\n\n<code>{name}</code>\n"
    start_time = datetime.now()
    file_path = ospath.join(Paths.down_path, name)
    
    try:
        await message.download(progress=lambda current, total: download_progress(current, total, start_time), 
                               in_memory=False, file_name=file_path)
        Transfer.down_bytes.append(media.file_size)
    except Exception as e:
        logging.error(f"Error downloading media: {e}")

# Example usage:
# link = "https://t.me/c/123456/789"
# num = 1
# await telegram_download(link, num)
