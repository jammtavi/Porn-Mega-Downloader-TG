import asyncio
import os
import json
from pathlib import Path
import subprocess
import youtube_dl
from pornhub_api import PornhubApi
from pornhub_api.backends.aiohttp import AioHttpBackend
from pyrogram import Client, filters
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


# Queue Downloads

async def Download_Porn_Video(client, message, link):
    msg = await message.reply_text(f"**Link:-** {link}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True)
    user_id = message.from_user.id

    ydl_opts = {
        "progress_hooks": [lambda d: download_progress_hook(d, msg, client)]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await run_async(ydl.download, [link])
        except DownloadError:
            await message.edit("Sorry, There was a problem with that particular video")
            return

    for file in os.listdir('.'):
        if file.endswith(".mkv") or file.endswith('.mp4'):
            await client.send_video(user_id, f"{file}",  caption=f"**File Name:- {file}\n\nHere Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}", reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
            os.remove(f"{file}")
            break
        else:
            continue

    await msg.delete()

    if link == queue_links[user_id][len(queue_links[user_id])-1]:
        queue_links.pop(user_id)
        await message.reply_text("ALL LINKS DOWNLOADED SUCCESSFULLY ✅")


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


@Client.on_message(link_filter)
async def download_video(client: Client, message: Message):
    if not await is_subscribed(client, message):
        return await force_sub(client, message)

    url = message.text
    msg = await message.reply_text(f"**Link:-** {url}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True, reply_to_message_id=message.id)
    user_id = message.from_user.id

    if user_id in active_list:
        if user_id not in queue_links:
            queue_links.update({user_id: [url]})

        else:
            queue_links[user_id].append(url)

        await msg.edit(f"Sorry! You can download only one video at a time\n\n⚠️ But Don't worry this files is added to queue when download is completed it'll start downloading one by one ✅")
        return
    else:
        active_list.append(user_id)

    ydl_opts = {
        "progress_hooks": [lambda d: download_progress_hook(d, msg, client)]
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            await run_async(ydl.download, [url])
        except DownloadError:
            await msg.edit("Sorry, There was a problem with that particular video")
            return

    for file in os.listdir('.'):
        if file.endswith(".mkv") or file.endswith('mp4'):
            await client.send_video(user_id, f"{file}", caption=f"**File Name:- {file}\n\nHere Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}", reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
            os.remove(f"{file}")
            break
        else:
            continue

    await msg.delete()
    active_list.remove(user_id)

    for link in queue_links[user_id]:
        try:
            await Download_Porn_Video(client, message, link)
        except Exception as e:
            print(e)
