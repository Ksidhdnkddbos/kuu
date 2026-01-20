from YMusic import app
from YMusic.core import userbot
from YMusic.utils.queue import add_to_queue, get_queue_length, is_queue_empty, get_queue, MAX_QUEUE_SIZE, get_current_song, QUEUE
from YMusic.utils.utils import delete_file, send_song_info
from YMusic.plugins.sounds.current import start_play_time, stop_play_time
from YMusic.misc import SUDOERS
from YMusic.filters import command
from pyrogram import filters
from pyrogram.types import Message
import time
import config
import asyncio
import os

# متغير لمنع الطلبات المتزامنة
current_requests = {}

async def process_audio_fast(title, duration, audio_file, link, 
                           requester_name, requester_id, chat_id, m):
    """معالجة وتشغيل فوري بدون global variables"""
    if duration is None:
        duration = 0
    
    # التحقق من المدة (سريع)
    if duration > 0 and duration > config.MAX_DURATION_MINUTES * 60:
        await m.edit("⦗ المدة طويلة جداً ⦘")
        if audio_file and os.path.exists(audio_file):
            await delete_file(audio_file)
        return
        
    # التحقق من قائمة الانتظار (سريع)
    queue_length = get_queue_length(chat_id)
    if queue_length >= MAX_QUEUE_SIZE:
        await m.edit("⦗ قائمة الانتظار ممتلئة ⦘")
        if audio_file and os.path.exists(audio_file):
            await delete_file(audio_file)
        return

    # إضافة للقائمة
    queue_num = add_to_queue(chat_id, title, duration, audio_file, link, 
                           requester_name, requester_id, False)
    
    if queue_num == 1:
        # تشغيل الملف فوراً
        Status, Text = await userbot.playAudio(chat_id, audio_file)

        if not Status:
            await m.edit(Text)
            if chat_id in QUEUE and QUEUE[chat_id]:
                QUEUE[chat_id].pop(0)  # إصلاح: pop بدل popleft
            return
        
        await start_play_time(chat_id)
        await send_song_info(chat_id, {
            'title': title,
            'duration': duration,
            'link': link,
            'requester_name': requester_name,
            'requester_id': requester_id
        })
        await m.delete()
    else:
        await m.edit(
            f"⦗ #{queue_num} في قائمة الانتظار ⦘\n"
            f"طلب: [{requester_name}](tg://user?id={requester_id})"
        )

async def ultra_fast_bot_check(query: str, bot_username: str, is_w60y: bool = False):
    """فحص فوري كل 0.3 ثانية - أقصى سرعة"""
    try:
        start_time = time.time()
        
        # إرسال الطلب
        if is_w60y:
            await app.send_message(bot_username, f"يوت {query}")
            # انضمام سريع للقناة
            try:
                await app.join_chat("@B_a_r")
            except:
                pass
        else:
            await app.send_message(bot_username, query)
        
        # المراقبة الفورية كل 0.3 ثانية
        max_checks = 20  # 20 فحص × 0.3 = 6 ثواني
        last_msg_id = 0
        
        for check_num in range(max_checks):
            # الحصول على آخر رسالة فقط (أسرع طريقة)
            try:
                async for msg in app.get_chat_history(bot_username, limit=1):
                    # التحقق إذا كانت الرسالة جديدة ولها مقطع صوتي
                    if msg.id > last_msg_id and (msg.audio or msg.voice):
                        elapsed = time.time() - start_time
                        print(f"⚡ {bot_username} رد بعد {elapsed:.1f} ثانية (فحص #{check_num})")
                        
                        last_msg_id = msg.id
                        
                        # تحميل فوري
                        audio_file = await msg.download()
                        
                        # معلومات سريعة
                        if msg.audio:
                            title = msg.audio.title or query
                            duration = msg.audio.duration
                        else:
                            title = query
                            duration = msg.voice.duration
                        
                        return audio_file, title, duration
            except Exception as e:
                print(f"⚠️ خطأ في فحص {bot_username}: {e}")
            
            # انتظار 0.3 ثانية فقط
            await asyncio.sleep(0.3)
        
        print(f"⏰ {bot_username} لم يرد خلال {max_checks * 0.3:.1f} ثانية")
        return None, None, None
        
    except Exception as e:
        print(f"❌ خطأ في ultra_fast_bot_check: {e}")
        return None, None, None

async def try_multiple_bots_ultra_fast(query: str):
    """محاولة مع عدة بوتات بأقصى سرعة"""
    bots_to_try = [
        ("@W60yBot", True),   # (بوت, هل يحتاج "يوت"؟)
        ("@BaarxXxbot", False),
        ("@vid", False),
        ("@musicder_bot", False),
    ]
    
    for bot_username, needs_yout in bots_to_try:
        print(f"🚀 محاولة فورية مع {bot_username}")
        
        audio_file, title, duration = await ultra_fast_bot_check(
            query, bot_username, needs_yout
        )
        
        if audio_file:
            print(f"✅ نجح مع {bot_username}")
            return audio_file, title, duration
    
    return None, None, None

@app.on_message(command(["فوري", "شغل", "تشغيل", "play", "شغلنا"]))
async def ultra_fast_play(_, message: Message):
    chat_id = message.chat.id
    
    # منع طلبات متزامنة لنفس الشات
    if chat_id in current_requests and time.time() - current_requests[chat_id] < 5:
        await message.reply("⏳ جارٍ معالجة طلب سابق، انتظر قليلاً...")
        return
    
    # وضع علامة على الطلب الحالي
    current_requests[chat_id] = time.time()
    
    # الحالة 1: رد على مقطع صوتي (فوري)
    if message.reply_to_message and (message.reply_to_message.audio or message.reply_to_message.voice):
        m = await message.reply_text("⚡ جاري التشغيل...")
        
        try:
            # تحميل فوري مباشر
            audio_file = await message.reply_to_message.download()
            
            # استخراج معلومات سريعة
            if message.reply_to_message.audio:
                title = message.reply_to_message.audio.title or "مقطع صوتي"
                duration = message.reply_to_message.audio.duration
            else:
                title = "رسالة صوتية"
                duration = message.reply_to_message.voice.duration
            
            link = message.reply_to_message.link
            
            # معالجة سريعة
            await process_audio_fast(
                title, duration, audio_file, link,
                message.from_user.first_name if message.from_user else "مستخدم",
                message.from_user.id if message.from_user else "1121532100",
                chat_id, m
            )
            
        except Exception as e:
            await m.edit(f"❌ خطأ: {str(e)}")
        
        finally:
            # إزالة علامة الطلب
            if chat_id in current_requests:
                del current_requests[chat_id]
        
        return
    
    # الحالة 2: بحث عن أغنية
    elif len(message.command) > 1:
        query = " ".join(message.command[1:])
        m = await message.reply_text(f"⚡ فوري: {query}")
        
        try:
            # محاولة فورية مع جميع البوتات
            audio_file, title, duration = await try_multiple_bots_ultra_fast(query)
            
            if not audio_file:
                await m.edit("❌ لم أجد الأغنية بسرعة")
                return
            
            # معالجة سريعة
            link = f"طلب: {query}"
            
            await process_audio_fast(
                title or query,
                duration or 0,
                audio_file,
                link,
                message.from_user.first_name if message.from_user else "مستخدم",
                message.from_user.id if message.from_user else "1121532100",
                chat_id, m
            )
            
        except Exception as e:
            await m.edit(f"❌ خطأ: {str(e)}")
            print(f"خطأ في التشغيل الفوري: {e}")
        
        finally:
            # إزالة علامة الطلب
            if chat_id in current_requests:
                del current_requests[chat_id]
    
    else:
        await message.reply_text("⚡ اكتب اسم الأغنية بعد الأمر")
        if chat_id in current_requests:
            del current_requests[chat_id]

# وظيفة تنظيف الطلبات القديمة (اختياري)
async def cleanup_old_requests():
    """تنظيف الطلبات القديمة كل دقيقة"""
    while True:
        await asyncio.sleep(60)
        current_time = time.time()
        old_requests = [
            chat_id for chat_id, req_time in current_requests.items()
            if current_time - req_time > 30  # أكثر من 30 ثانية
        ]
        for chat_id in old_requests:
            del current_requests[chat_id]

# بدء التنظيف عند تشغيل البوت
@app.on_startup()
async def startup():
    asyncio.create_task(cleanup_old_requests())

# باقي الأوامر (تعديلها بنفس المنطق)
@app.on_message(command(["ايقاف", "stop"]))
async def stop_command(_, message: Message):
    chat_id = message.chat.id
    Text = await userbot.stop(chat_id)
    
    # تنظيف
    if chat_id in QUEUE:
        del QUEUE[chat_id]
    if chat_id in current_requests:
        del current_requests[chat_id]
    
    await message.reply_text(Text)
        
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
