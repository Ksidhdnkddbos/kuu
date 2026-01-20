
from YMusic import app
from YMusic.core import userbot
from YMusic.utils.queue import add_to_queue, get_queue_length, is_queue_empty, get_queue, MAX_QUEUE_SIZE, get_current_song, QUEUE
from YMusic.utils.utils import delete_file, send_song_info
from YMusic.utils.formaters import get_readable_time, format_time
from YMusic.plugins.sounds.current import start_play_time, stop_play_time
from YMusic.misc import SUDOERS
from YMusic.filters import command
from pyrogram import filters
from pyrogram.types import Message
import time
import config
import asyncio
import os

# متغيرات عامة لاستخدامها في دالة process_audio
global_m = None
global_chat_id = None
global_requester_id = None
global_requester_name = None

async def process_audio(title, duration, audio_file, link):
    """معالجة وتشغيل المقطع الصوتي"""
    global global_m, global_chat_id, global_requester_id, global_requester_name
    
    if duration is None:
        duration = 0
    
    # التحقق من المدة
    if duration > 0 and duration > config.MAX_DURATION_MINUTES * 60:
        await global_m.edit(f"⦗ المدة طويلة جداً ⦘")
        if audio_file and os.path.exists(audio_file):
            await delete_file(audio_file)
        return
        
    # التحقق من قائمة الانتظار
    queue_length = get_queue_length(global_chat_id)
    if queue_length >= MAX_QUEUE_SIZE:
        await global_m.edit(f"⦗ قائمة الانتظار ممتلئة ⦘")
        if audio_file and os.path.exists(audio_file):
            await delete_file(audio_file)
        return

    # إضافة للقائمة
    queue_num = add_to_queue(global_chat_id, title, duration, audio_file, link, 
                           global_requester_name, global_requester_id, False)
    
    if queue_num == 1:
        # تشغيل الملف
        Status, Text = await userbot.playAudio(global_chat_id, audio_file)

        if not Status:
            await global_m.edit(Text)
            if global_chat_id in QUEUE and QUEUE[global_chat_id]:
                QUEUE[global_chat_id].popleft()
            return
        
        await start_play_time(global_chat_id)
        await send_song_info(global_chat_id, {
            'title': title,
            'duration': duration,
            'link': link,
            'requester_name': global_requester_name,
            'requester_id': global_requester_id
        })
        await global_m.delete()
    else:
        await global_m.edit(
            f"- بالرقم التالي #{queue_num} \n\n"
            f"- تم اضافتها الى قائمة الانتظار \n"
            f"- بطلب من : [{global_requester_name}](tg://user?id={global_requester_id})"
        )

async def get_audio_response_from_bot(query: str):
    """التنزيل من البوت @W60yBot"""
    try:
        print(f"🔍 محاولة مع @W60yBot للبحث عن: {query}")
        
        # 1. الانضمام للقناة أولاً
        try:
            await app.join_chat("@B_a_r")
            await asyncio.sleep(1)
        except:
            pass
        
        # 2. إرسال رسالة للبوت مباشرة
        await app.send_message("@W60yBot", f"يوت {query}")
        
        # 3. الانتظار قليلاً للبوت ليرسل المقطع
        await asyncio.sleep(5)
        
        # 4. الحصول على آخر رسائل البوت
        messages = []
        async for message in app.get_chat_history("@W60yBot", limit=15):
            if message.from_user and message.from_user.username == "W60yBot":
                messages.append(message)
                if len(messages) >= 5:  # نأخذ آخر 5 رسائل فقط
                    break
        
        # 5. البحث عن المقطع الصوتي (الأحدث أولاً)
        for msg in messages:
            if msg.audio or msg.voice:
                print(f"✅ وجدت مقطع صوتي: {msg.id}")
                
                # تحميل المقطع
                audio_file = await msg.download()
                
                # استخراج المعلومات
                if msg.audio:
                    title = msg.audio.title or query
                    duration = msg.audio.duration
                else:
                    title = query
                    duration = msg.voice.duration
                
                return audio_file, title, duration
        
        return None, None, None
        
    except Exception as e:
        print(f"❌ خطأ في get_audio_response_from_bot: {str(e)}")
        return None, None, None

async def try_baar_bot(query: str):
    """محاولة مع البوت الثاني @BaarxXxbot"""
    try:
        print(f"🔍 محاولة مع @BaarxXxbot للبحث عن: {query}")
        
        # إرسال رسالة للبوت
        await app.send_message("@BaarxXxbot", query)
        
        # الانتظار
        await asyncio.sleep(5)
        
        # الحصول على آخر رسائل البوت
        messages = []
        async for message in app.get_chat_history("@BaarxXxbot", limit=10):
            if message.from_user and message.from_user.username == "BaarxXxbot":
                messages.append(message)
                if len(messages) >= 5:
                    break
        
        # البحث عن المقطع الصوتي
        for msg in messages:
            if msg.audio or msg.voice:
                print(f"✅ وجدت مقطع صوتي من @BaarxXxbot: {msg.id}")
                
                audio_file = await msg.download()
                
                if msg.audio:
                    title = msg.audio.title or query
                    duration = msg.audio.duration
                else:
                    title = query
                    duration = msg.voice.duration
                
                return audio_file, title, duration
        
        return None, None, None
        
    except Exception as e:
        print(f"❌ خطأ في try_baar_bot: {str(e)}")
        return None, None, None

@app.on_message(command(["شغلنا", "GG", "شغل", "تشغيل"]))
async def _aPlay(_, message: Message):
    global global_m, global_chat_id, global_requester_id, global_requester_name
    
    global_chat_id = message.chat.id
    global_requester_id = message.from_user.id if message.from_user else "1121532100"
    global_requester_name = message.from_user.first_name if message.from_user else None
    
    # الحالة 1: رد على مقطع صوتي (الكود الأصلي)
    if message.reply_to_message and (message.reply_to_message.audio or message.reply_to_message.voice):
        global_m = await message.reply_text("⦗ جارٍ التنفيذ ... ⦘")
        
        # ⭐ التحميل المباشر من الرد
        audio_file = await message.reply_to_message.download()
        
        # ⭐ استخراج المعلومات من الرد
        if message.reply_to_message.audio:
            title = message.reply_to_message.audio.title if message.reply_to_message.audio else "Voice Message"
            duration = message.reply_to_message.audio.duration if message.reply_to_message.audio else 0
        else:
            title = "Voice Message"
            duration = message.reply_to_message.voice.duration
            
        link = message.reply_to_message.link
        
        # ⭐ نفس المعالجة
        await process_audio(title, duration, audio_file, link)
        return
    
    # الحالة 2: بحث عن أغنية
    elif len(message.command) > 1:
        query = " ".join(message.command[1:])
        global_m = await message.reply_text("⦗ انتضر قليلاً ... ⦘")
        
        try:
            # 1. محاولة مع @W60yBot أولاً
            audio_file, title, duration = await get_audio_response_from_bot(query)
            
            # 2. إذا فشل، نجرب @BaarxXxbot
            if not audio_file:
                audio_file, title, duration = await try_baar_bot(query)
            
            if not audio_file:
                await global_m.edit("⦗ لم يتم العثور على نتيجة ⦘")
                return
            
            await global_m.edit("⦗ جارٍ التنفيذ ... ⦘")
            
            # 3. التأكد من وجود القيم
            if not title:
                title = query
            if not duration:
                duration = 0
                
            link = f"https://t.me/{message.from_user.username}" if message.from_user else "طلب مباشر"
            
            # 4. ⭐⭐ نفس المعالجة! ⭐⭐
            await process_audio(title, duration, audio_file, link)
            
        except Exception as e:
            await global_m.edit(f"<code>Error: {e}</code>")
            print(f"خطأ في _aPlay: {e}")
    
    else:
        await message.reply_text("⦗ اكتب اسم الأغنية بعد الأمر ⦘")
        
@app.on_message(command(["قائمة التشغيل", "الطابور", "قائمة الانتضار", "القائمة"]))
async def _playlist(_, message):
    chat_id = message.chat.id
    if is_queue_empty(chat_id):
        await message.reply_text(" لايوجد شي في قائمة التشغيل .")
    else:
        queue = get_queue(chat_id)
        playlist = "- هذا هي قائمة التشغيل :\n\n"
        for i, song in enumerate(queue, start=1):
            duration = song['duration']
            duration_str = format_time(duration)

            if i == 1:
                playlist += f"{i}. ▶️ {song['title']} - {duration_str}\n"
                playlist += f"- طلب : [{song['requester_name']}](tg://user?id={song['requester_id']})\n\n"
            else:
                playlist += f"{i}. {song['title']} - {duration_str}\n"
                playlist += f"- طلب : [{song['requester_name']}](tg://user?id={song['requester_id']})\n\n"
            
            if i == MAX_QUEUE_SIZE:
                break
        
        if len(queue) > MAX_QUEUE_SIZE:
            playlist += f"\nDan {len(queue) - MAX_QUEUE_SIZE} lagu lainnya..."
        
        await message.reply_text(playlist, disable_web_page_preview=True)

@app.on_message(command(["ف", "فيد", "فيديو"]))
async def _vPlay(_, message):
    start_time = time.time()
    chat_id = message.chat.id
    requester_id = message.from_user.id if message.from_user else "1121532100"
    requester_name = message.from_user.first_name if message.from_user else None

    async def process_video(title, duration, video_file, link):
        if duration is None:
            duration = 0  
        duration_minutes = duration / 60 if isinstance(duration, (int, float)) else 0

        if duration_minutes > config.MAX_DURATION_MINUTES:
            await m.edit(f"⦗ اعتذر ولكن المدة الاقصى للتشغيل هي {config.MAX_DURATION_MINUTES} دقيقة ⦘")
            await delete_file(video_file)
            return

        queue_length = get_queue_length(chat_id)
        if queue_length >= MAX_QUEUE_SIZE:
            await m.edit(f"⦗ قائمة الانتظار ممتلئة جداً وعددها {MAX_QUEUE_SIZE} \n يرجى الانتظار بعض الوقت من فضلك ⦘")
            await delete_file(video_file)
            return

        queue_num = add_to_queue(chat_id, title, duration, video_file, link, requester_name, requester_id, True)
        if queue_num == 1:
            Status, Text = await userbot.playVideo(chat_id, video_file)
            if not Status:
                await m.edit(Text)
            else:
                finish_time = time.time()
                await start_play_time(chat_id)
                total_time_taken = str(int(finish_time - start_time)) + "s"
                
                current_video = {
                    'title': title,
                    'duration': duration,
                    'link': link,
                    'requester_name': requester_name,
                    'requester_id': requester_id
                }
                
                await send_video_info(chat_id, current_video)
                await m.delete()
        elif queue_num:
            await m.edit(f"- بالرقم التالي #{queue_num} \n\n- تم اضافتها الى قائمة الانتضار \n- بطلب من : [{requester_name}](tg://user?id={requester_id})")
        else:
            await m.edit(f"- فشلت الإضافة الى الطابور، اعتقد بأن الطابور ممتلئ .")

    try:
        if message.reply_to_message and (message.reply_to_message.video or message.reply_to_message.video_note):
            m = await message.reply_text("⦗ جارٍ التنفيذ ... ⦘")
            video_file = await message.reply_to_message.download()
            title = "Video File"
            duration = message.reply_to_message.video.duration if message.reply_to_message.video else 0
            link = message.reply_to_message.link

            if duration > config.MAX_DURATION_MINUTES * 60:
                await m.edit(f"⦗ اعتذر ولكن المدة الاقصى للتشغيل هي {config.MAX_DURATION_MINUTES} دقيقة ⦘")
                await delete_file(video_file)
                return
            
            asyncio.create_task(process_video(title, duration, video_file, link))

        elif len(message.command) < 2:
            await message.reply_text("""- عزيزنا ارسل "الاوامر" لمعرفة اوامر التشغيل .""")

        else:
            m = await message.reply_text("⦗ انتظر قليلاً ... ⦘")
            original_query = message.text.split(maxsplit=1)[1]

            if "youtube.com" in original_query or "youtu.be" in original_query:
                video_id = extract_video_id(original_query)  
                title, duration, link = await searchYt(video_id)
            else:
                title, duration, link = await searchYt(original_query)  

            if not title:
                return await m.edit("⦗ لم يتم العثور على نتيجة ⦘")

            if duration is not None:
                duration_minutes = duration / 60
                if duration_minutes > config.MAX_DURATION_MINUTES:
                    await m.edit(f"⦗ اعتذر ولكن المدة الاقصى للتشغيل هي {config.MAX_DURATION_MINUTES} دقيقة ⦘")
                    return

            await m.edit("⦗ جارٍ التنفيذ ... ⦘")
            file_name = f"{title}"
            video_file, downloaded_title, video_duration = await download_video(link, file_name)

            if not video_file:
                return await m.edit("فشل في تنزيل الفيديو ...")

            if video_duration is not None and video_duration > config.MAX_DURATION_MINUTES * 60:
                await m.edit(f"⦗ اعتذر ولكن المدة الاقصى للتشغيل هي {config.MAX_DURATION_MINUTES} دقيقة ⦘")
                await delete_file(video_file)
                return

            asyncio.create_task(process_video(downloaded_title, video_duration, video_file, link))

    except Exception as e:
        await message.reply_text(f"<code>Error: {e}</code>")

async def send_video_info(chat_id, current_video):
    title = current_video['title']
    duration = current_video['duration']
    link = current_video['link']
    requester_name = current_video['requester_name']
    requester_id = current_video['requester_id']

    await app.send_message(
        chat_id,
        f"⦗ تم بدء تشغيل الفيديو بأمر [{requester_name}](tg://user?id={requester_id}) ⦘\n"
        f"⎯ ⎯ ⎯ ⎯\n"
        f"- لمعرفة المزيد ارسل \"الاوامر\"\n"
        f"🪬 تابعنا : [Click .](https://t.me/{DEV_CHANNEL})",
        disable_web_page_preview=True  
    )
