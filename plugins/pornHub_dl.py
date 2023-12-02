import asyncio
import os
import json
from pathlib import Path
import subprocess
import sys
import youtube_dl
from pornhub_api import PornhubApi
from pornhub_api.backends.aiohttp import AioHttpBackend
from pyrogram import Client, filters, StopPropagation
from pyrogram.errors.exceptions import UserNotParticipant
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, InlineQuery,
                            InlineQueryResultArticle, InputTextMessageContent,
                            Message)
from youtube_dl.utils import DownloadError
from helper.utils import force_sub, is_subscribed
from config import Config
from helper.utils import download_progress_hook


config_path = Path("config.json")
if os.path.exists("downloads"):
    print("Download Path Exist")
else:
    print("Download Path Created")

btn1 = InlineKeyboardButton(
    "Search Here", switch_inline_query_current_chat="",)
btn2 = InlineKeyboardButton("Go Inline", switch_inline_query="")

active_list = []
queue_links = {}
index = 0

# Queue Downloads


async def Download_Porn_Video(client, callback, link_msg):
    global index
    user_id = callback.from_user.id

    msg = await callback.message.reply_text(f"**Link:-** {queue_links[user_id][index]}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True)

    ydl_opts = {
        "progress_hooks": [lambda d: download_progress_hook(d, msg, client)]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await run_async(ydl.download, [queue_links[user_id][index]])
        except DownloadError:
            await msg.edit("Sorry, There was a problem with that particular video")
            return

    for file in os.listdir('.'):
        if file.endswith(".mkv") or file.endswith('.mp4'):
            await client.send_video(user_id, f"{file}",  caption=f"**File Name:- {file}\n\nHere Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}", reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
            os.remove(f"{file}")
            break
        else:
            continue

    await msg.delete()

    if queue_links[user_id][index] == queue_links[user_id][len(queue_links[user_id])-1]:
        queue_links.pop(user_id)
        index = 0
        try:
            await callback.message.reply_text(f"ALL LINKS DOWNLOADED SUCCESSFULLY ✅", reply_to_message_id=link_msg.id)
            return
        except:
            await callback.message.reply_text(f"ALL LINKS DOWNLOADED SUCCESSFULLY ✅")

    else:
        index += 1
        await Download_Porn_Video(client=client, callback=callback, link_msg=link_msg)


async def run_async(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    print("This is loop", loop)
    return await loop.run_in_executor(None, func, *args, **kwargs)


def link_fil(filter, client, update):
    if "https://www.pornhub" in update.text:
        return True
    else:
        return False


link_filter = filters.create(link_fil, name="link_filter")


@Client.on_inline_query()
async def search(client, InlineQuery: InlineQuery):
    query = InlineQuery.query
    backend = AioHttpBackend()
    api = PornhubApi(backend=backend)
    results = []
    try:
        src = await api.search.search(query)  # , ordering="mostviewed")
    except ValueError as e:
        results.append(InlineQueryResultArticle(
            title="No Such Videos Found!",
            description="Sorry! No Such Vedos Were Found. Plz Try Again",
            input_message_content=InputTextMessageContent(
                message_text="No Such Videos Found!"
            )
        ))
        await InlineQuery.answer(results,
                                 switch_pm_text="Search Results",
                                 switch_pm_parameter="start")

        return

    videos = src.videos
    await backend.close()

    for vid in videos:

        try:
            pornstars = ", ".join(v for v in vid.pornstars)
            categories = ", ".join(v for v in vid.categories)
            tags = ", #".join(v for v in vid.tags)
        except:
            pornstars = "N/A"
            categories = "N/A"
            tags = "N/A"
        msgg = (f"**TITLE** : `{vid.title}`\n"
                f"**DURATION** : `{vid.duration}`\n"
                f"VIEWS : `{vid.views}`\n\n"
                f"**{pornstars}**\n"
                f"Categories : {categories}\n\n"
                f"{tags}"
                f"Link : {vid.url}")

        msg = f"{vid.url}"

        results.append(InlineQueryResultArticle(
            title=vid.title,
            input_message_content=InputTextMessageContent(
                message_text=msg,
            ),
            description=f"Duration : {vid.duration}\nViews : {vid.views}\nRating : {vid.rating}",
            thumb_url=vid.thumb,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Watch online", url=vid.url),
                btn1
            ]]),
        ))

    await InlineQuery.answer(results,
                             switch_pm_text="Search Results",
                             switch_pm_parameter="start")


@Client.on_message(link_filter & filters.user(Config.ADMIN))
async def options(client, message: Message):

    # deleting things before downloading if it's available
    try:
        for file in os.listdir('.'):
            if file.endswith('.mp4') or file.endswith('.mkv'):
                os.remove(file)

        if message.from_user.id in queue_links:
            queue_links.pop(message.from_user.id)

        elif message.from_user.id in active_list:
            active_list.remove(message.from_user.id)

    except:
        pass

    await message.reply("What would like to do?", reply_to_message_id=message.id,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="🔻 Download 🔻", callback_data= f"d_{message.text}"), InlineKeyboardButton(text="➕ Add Multiple Links ➕", callback_data=f"m_{message.text}")],
                                                           [InlineKeyboardButton(
                                                               text="📺 Watch Video 📺    ",url=message.text)]
                                                           ])
                        )


@Client.on_callback_query(filters.regex("^d"))
async def single_download(client, callback: CallbackQuery):
    url = callback.data.split("_", 1)[1]
    msg = await callback.message.edit(f"**Link:-** {url}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True)
    user_id = callback.from_user.id

    if user_id in active_list:
        await callback.message.edit("Sorry! You can download only one video at a time")
        return
    else:
        active_list.append(user_id)

    ydl_opts = {
        "progress_hooks": [lambda d: download_progress_hook(d, callback.message, client)]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await run_async(ydl.download, [url])
        except DownloadError:
            await callback.message.edit("Sorry, There was a problem with that particular video")
            return

    for file in os.listdir('.'):
        if file.endswith(".mp4") or file.endswith('.mkv'):
            await callback.message.reply_video(f"{file}", caption=f"**Here Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}",
                                               reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
            os.remove(f"{file}")
            break
        else:
            continue

    await msg.delete()
    active_list.remove(user_id)


@Client.on_callback_query(filters.regex("^m"))
async def multiple_download(client, callback: CallbackQuery):
    try:
        global queue_links
        user_id = callback.from_user.id

        if user_id not in queue_links:
            queue_links.update({user_id: [callback.data.split('_', 1)[1]]})
            while True:
                link = await client.ask(chat_id=user_id, text="🔗Send Link to add it to queue 🔗\n\nUse /done when you're done adding links to queue.", filters=filters.text)

                if str(link.text).startswith("https://www.pornhub"):
                    queue_links[user_id].append(link.text)
                    await callback.message.reply_text("Successfully Added To Queue ✅", reply_to_message_id=link.id)

                elif link.text == "/done":
                    user = queue_links[user_id]
                    links = ""
                    for idx, link in enumerate(user):
                        links += f"{(idx+1)}. {link}\n"

                    links_msg = await callback.message.reply_text(f"👤 <code>{callback.from_user.first_name}</code>\n\n <code>{links}</code>")
                    break

                else:
                    callback.answer("⚠️ Please Send Valid Link !")
                    continue
                

        await callback.message.reply_text("Downloading Started ✅\n\nPlease have patience while it's downloading it may take sometimes...")

        if user_id in queue_links:
            try:
                await Download_Porn_Video(client, callback, links_msg)
            except Exception as e:
                print(e)

    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command('cc'))
async def send_queue(client, message):
    await message.reply_text(f"Queue List :- {queue_links}\n\n Index :- {index}\n\n Active List :- {active_list}")
