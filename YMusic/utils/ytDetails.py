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
        file.write(f'Chosen File: {cookie_txt_file}\n')
    return cookie_txt_file

async def searchYt(query):
    ydl_opts = {
        'quiet': True,
        'cookiefile': cookie_txt_file(),
        'noplaylist': True,
        'default_search': 'ytsearch1',
        'dump_single_json': True,
    }

    try:
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

async def download_audio(link, file_name):
    output_path = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': os.path.join(output_path, f'{file_name}.%(ext)s'),
        'cookiefile': cookie_txt_file(),
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'buffer-size': '256M',  
        'http_chunk_size': 16 * 1024 * 1024,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-k', '1M'],  
        'quiet': True,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([link]))

        output_file = os.path.join(output_path, f'{file_name}.mp3')
        if not os.path.exists(output_file):
            raise Exception(f"File not downloaded successfully: {output_file}")
        
        return output_file, file_name, None
    except Exception as e:
        print(f"Error in download_audio: {e}")
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
        'buffer-size': '256M', 
        'http_chunk_size': 16 * 1024 * 1024,  
        'external_downloader': 'aria2c',  
        'external_downloader_args': ['-x', '16', '-k', '1M'],  
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