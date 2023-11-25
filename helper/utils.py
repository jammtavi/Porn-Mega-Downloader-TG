import math
import time
from datetime import datetime
from pytz import timezone
from pyrogram.errors.exceptions import MessageNotModified, FloodWait, UserNotParticipant
from pyrogram import enums
import asyncio
import logging
import threading
from youtube_dl.utils import DownloadError
import youtube_dl
import os
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["⬢" for i in range(math.floor(percentage / 5))]),
            ''.join(["⬡" for i in range(20 - math.floor(percentage / 5))])
        )
        tmp = progress + Txt.PROGRESS_BAR.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text=f"{ud_type}\n\n{tmp}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("✖️ 𝙲𝙰𝙽𝙲𝙴𝙻 ✖️", callback_data="close")]])
            )
        except:
            pass


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "ᴅ, ") if days else "") + \
        ((str(hours) + "ʜ, ") if hours else "") + \
        ((str(minutes) + "ᴍ, ") if minutes else "") + \
        ((str(seconds) + "ꜱ, ") if seconds else "") + \
        ((str(milliseconds) + "ᴍꜱ, ") if milliseconds else "")
    return tmp[:-2]


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


async def send_log(b, u):
    if Config.LOG_CHANNEL is not None:
        curr = datetime.now(timezone("Asia/Kolkata"))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        await b.send_message(
            Config.LOG_CHANNEL,
            f"**--Nᴇᴡ Uꜱᴇʀ Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ--**\n\nUꜱᴇʀ: {u.mention}\nIᴅ: `{u.id}`\nUɴ: @{u.username}\n\nDᴀᴛᴇ: {date}\nTɪᴍᴇ: {time}\n\nBy: {b.mention}"
        )


def humanbytes(size):
    """Convert Bytes To Bytes So That Human Can Read It"""
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


def edit_msg(client, message, to_edit):
    try:
        client.loop.create_task(message.edit(to_edit))
    except MessageNotModified:
        pass
    except FloodWait as e:
        client.loop.create_task(asyncio.sleep(e.value))
    except TypeError:
        pass


def download_progress_hook(d, message, client):
    if d['status'] == 'downloading':
        current = d.get("_downloaded_bytes_str") or humanbytes(
            int(d.get("downloaded_bytes", 1)))
        total = d.get("_total_bytes_str") or d.get("_total_bytes_estimate_str")
        file_name = d.get("filename")
        eta = d.get('_eta_str', "N/A")
        percent = d.get("_percent_str", "N/A")
        speed = d.get("_speed_str", "N/A")
        to_edit = f"<b><u>Downloading File</b></u> \n<b>File Name :</b> <code>{file_name}</code> \n<b>File Size :</b> <code>{total}</code> \n<b>Speed :</b> <code>{speed}</code> \n<b>ETA :</b> <code>{eta}</code> \n<i>Downloaded {current} out of {total}</i> (__{percent}__)"
        threading.Thread(target=edit_msg, args=(
            client, message, to_edit)).start()


async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(Config.AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True

    return False


async def force_sub(bot, cmd):
    invite_link = await bot.create_chat_invite_link(int(Config.AUTH_CHANNEL))
    buttons = [[InlineKeyboardButton(
        text="📢 Cont. Owner to add you in Channel 📢", url="https://t.me/V_Ditu")]]
    text = "**Sᴏʀʀy Dᴜᴅᴇ Yᴏᴜ'ʀᴇ Nᴏᴛ Jᴏɪɴᴇᴅ My Cʜᴀɴɴᴇʟ 😐. Sᴏ Pʟᴇᴀꜱᴇ Jᴏɪɴ Oᴜʀ Uᴩᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ Tᴏ Cᴄᴏɴᴛɪɴᴜᴇ**"

    return await cmd.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))


async def run_async(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    print("This is loop", loop)
    return await loop.run_in_executor(None, func, *args, **kwargs)


async def Download_Porn_Video(client, message, link):

    btn1 = InlineKeyboardButton(
        "Search Here", switch_inline_query_current_chat="",)
    btn2 = InlineKeyboardButton("Go Inline", switch_inline_query="")
    url = link
    msg = await message.reply_text("Downloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", reply_to_message_id=message.id)

    # user_id = message.from_user.id

    # if user_id in active_list:
    #     await msg.edit("Sorry! You can download only one video at a time")

    #     return
    # else:
    #     active_list.append(user_id)

    ydl_opts = {
        "progress_hooks": [lambda d: download_progress_hook(d, msg, client)],

    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await run_async(ydl.download, [url])
        except DownloadError:
            await msg.edit("Sorry, There was a problem with that particular video")
            return

    for file in os.listdir('.'):
        if file.endswith(".mp4"):
            if file.startswith(file):
                await client.send_video(message.from_user.id, f"{file}", caption=f"**File Name:- {file}\n\nHere Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}",
                                        reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
                os.remove(f"{file}")

            break
        else:
            continue

    await msg.delete()
    # active_list.remove(user_id)
    return True
