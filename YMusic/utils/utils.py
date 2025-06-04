import os
import glob
import re
import asyncio
import aiohttp
import json
import shutil
from urllib.parse import quote

from YMusic.utils.queue import QUEUE, add_to_queue
from YMusic import app
from YMusic.utils.formaters import format_time
from config import DEV_CHANNEL

MAX_MESSAGE_LENGTH = 4096

async def clear_downloads_cache():
    downloads_path = os.path.join(os.getcwd(), "downloads")
    try:
        shutil.rmtree(downloads_path)
        print(f"Removed directory: {downloads_path}")
    except FileNotFoundError:
        print(f"Directory not found: {downloads_path}")
    except Exception as e:
        print(f"Error removing directory {downloads_path}: {e}")
    try:
        os.mkdir(downloads_path)
        print(f"Created new directory: {downloads_path}")
    except Exception as e:
        print(f"Error creating directory {downloads_path}: {e}")

async def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File deleted successfully: {file_path}")
        else:
            print(f"File does not exist: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

async def send_song_info(chat_id, song, is_loop=False):
    original_query = song.get('query', song['title'])
    title = song['title']
    duration = song['duration']  # تأكد أن هذه القيمة بالثواني
    link = song['link']
    requester_name = song['requester_name']
    requester_id = song['requester_id']
    
    # تحويل المدة من ثواني إلى دقائق:ثواني
    minutes, seconds = divmod(int(duration), 60)
    formatted_duration = f"{minutes}:{seconds:02d}"
    
    # تنسيق الرسالة بشكل أفضل
    info_text = f"""
🎵 | تم التشغيل بنجاح

⦿ اسم الأغنية: [{title[:25]}]({link})
⦿ المدة: {formatted_duration}
⦿ طلب من: [{requester_name}](tg://user?id={requester_id})
"""
    await app.send_message(chat_id, info_text, disable_web_page_preview=True)
