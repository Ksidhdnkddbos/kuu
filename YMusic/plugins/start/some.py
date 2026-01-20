import time
import config
from YMusic import app
from YMusic.filters import command
from config import DEV_CHANNEL, DEV_USER
from pyrogram import filters 
from pyrogram import Client, filters
import re

@app.on_message(command("انضم"))
async def join_channel(client, message):
    if len(message.command) > 1:
        channel = message.command[1] 
        try:
            await client.join_chat(channel)
            await message.reply("- تم الانضمام بنجاح .")
        except Exception as e:
            await message.reply(f"حدث خطأ أثناء محاولة الانضمام: {str(e)}")
    else:
        await message.reply("يرجى توفير رابط أو معرف القناة بعد الأمر 'انضم'.")

@app.on_message(command(["البنك","بنك"]))
async def handle_bank_command(_, message):
    start_time = time.time()
    waiting_message = await message.reply_text("- انتظر قليلاً")
    end_time = time.time()
    latency = round((end_time - start_time) * 1000, 2)
    await waiting_message.delete() 
    await message.reply_text(f"- البنك هو {latency} مللي ثانية.")

@app.on_message(command(["سورس", "السورس","مطور السورس","المبرمج"]))
async def handle_source_command(_, message):
    source_info = (
        "- أهلا عزيزي في سورس آراس\n"
        "⎯ ⎯ ⎯ ⎯\n"
        "- معلومات السورس هي:\n"
        "- قناة السورس: [Click](https://t.me/aqhvv)\n"
        "- مطور السورس: [Click](https://t.me/lx5x5)\n\n"
        "- تم اصدار هذا السورس بموجب القانون 📍."
    )
    await message.reply_text(source_info, disable_web_page_preview=True)  

@app.on_message(command(["مطور", "المطور"]))
async def handle_developer_command(_, message):
    developer_info = (
        "- أهلا عزيزي، هذه هي معلومات المطور:\n"
        "⎯ ⎯ ⎯ ⎯\n"
        f"- قناة المطور : [Click](https://t.me/{DEV_CHANNEL})\n"
        f"- يوزر المطور : [Click](https://t.me/{DEV_USER})\n\n"
        "- تم إصدار هذا السورس بموجب القانون 📍."
    )
    await message.reply_text(developer_info, disable_web_page_preview=True)
