import os
import glob
import random
import json
import asyncio
import yt_dlp
from urllib.parse import urlparse, parse_qs

def cookie_txt_file():
    folder_path = f"{os.getcwd()}/cookies"
    filename = f"{os.getcwd()}/cookies/logs.csv"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    with open(filename, 'a') as file:
        file.write(f'Choosen File : {cookie_txt_file}\n')
    return cookie_txt_file

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_txt_file(),
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

async def searchYt(query):
    ydl_opts = {
        'quiet': True,
        'cookiefile': cookie_txt_file(),
        'noplaylist': True,
        'default_search': 'ytsearch1',  # Use yt-dlp's built-in search
        'dump_single_json': True,
    }

    try:
        # Execute yt-dlp search command
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(query, download=False))
        
        if not result or 'entries' not in result or len(result['entries']) == 0:
            return None, None, None

        video = result['entries'][0]
        title = video.get('title')
        duration_seconds = video.get('duration', 0)
        link = video.get('webpage_url')

        return title, duration_seconds, link
    except Exception as e:
        print(f"Error in searchYt: {e}")
        return None, None, None

import os
import yt_dlp
import asyncio

async def download_audio(link, file_name):
    output_path = os.path.join(os.getcwd(), "downloads")
    os.makedirs(output_path, exist_ok=True)  # أكثر أماناً من الشرط if
    
    ydl_opts = {
        # إعدادات التنزيل المثلى
        'format': 'bestaudio[ext=m4a]',  # اختيار أفضل صيغة صوت مباشرة
        'outtmpl': os.path.join(output_path, f'{file_name}.%(ext)s'),
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'cookiefile': cookie_txt_file(),
        
        # تحسينات الأداء
        'concurrent_fragment_downloads': 4,  # تنزيل أجزاء متعددة معاً
        'http_chunk_size': 1048576,  # 1MB لكل قطعة
        'retries': 3,  # تقليل عدد المحاولات
        
        # إعدادات التحويل
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',  # الأسرع في التحويل
        }],
        
        'verbose': False,  # إيقاف التفاصيل غير الضرورية
        'extract_flat': False,
    }

    try:
        start_time = time.time()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # تنزيل الملف مع عرض التقدم
            def progress_hook(d):
                if d['status'] == 'downloading':
                    print(f"\rDownloaded {d.get('downloaded_bytes',0)} bytes", end='')
            
            ydl.add_progress_hook(progress_hook)
            
            info = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: ydl.extract_info(link, download=True)
            )
            
            print(f"\nDownload completed in {time.time()-start_time:.2f} seconds")
            
            # الحصول على الملف المنزّل
            actual_ext = info.get('ext', 'm4a')
            downloaded_file = os.path.join(output_path, f'{file_name}.{actual_ext}')
            
            if not os.path.exists(downloaded_file):
                raise FileNotFoundError("Downloaded file not found")
            
            return downloaded_file, info.get('title', file_name), info.get('duration', 0)
            
    except Exception as e:
        print(f"\nError in download_audio: {str(e)}")
        # تنظيف الملفات غير المكتملة
        for f in glob.glob(os.path.join(output_path, f'{file_name}.*')):
            try: os.remove(f)
            except: pass
        return None, None, None
        
async def download_video(link, file_name):
    output_path = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_path, f'{file_name}.%(ext)s'),
        'cookiefile': cookie_txt_file(),  
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'buffer-size': '16M',
        'quiet': True,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([link]))

        output_file = os.path.join(output_path, f'{file_name}.mp4')
        if not os.path.exists(output_file):
            raise Exception(f"File not downloaded successfully: {output_file}")
        
        return output_file, file_name, None
    except Exception as e:
        print(f"Error in download_video: {e}")
        return None, None, None

def extract_playlist_id(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    playlist_id = query_params.get('list', [None])[0]
    return playlist_id

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        video_id = parsed_url.path[1:]
    else:
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [None])[0]
    return video_id
