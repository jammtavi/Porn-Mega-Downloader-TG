import asyncio
import os

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


if os.path.exists("downloads"):
    print("Download Path Exist")
else:
    print("Download Path Created")

btn1 = InlineKeyboardButton("Search Here",switch_inline_query_current_chat="",)
btn2 = InlineKeyboardButton("Go Inline", switch_inline_query="")

active_list = []
queue = []


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
async def search(client, InlineQuery : InlineQuery):
    query = InlineQuery.query
    backend = AioHttpBackend()
    api = PornhubApi(backend=backend)
    results = []
    try:
        src = await api.search.search(query)#, ordering="mostviewed")
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
async def options(client, message : Message):
    if not await is_subscribed(client, message):
        return await force_sub(client, message)
    await message.reply("What would like to do?", reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text= "🔻 Download 🔻", callback_data= f"d_{message.text}"), InlineKeyboardButton(text="📺 Watch Video 📺",url=message.text)]
            ])
            )


@Client.on_callback_query(filters.regex("^d"))
async def download_video(client, callback : CallbackQuery):
    url = callback.data.split("_",1)[1]
    msg = await callback.message.edit("Downloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...")
    user_id = callback.message.from_user.id

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
        if file.endswith(".mp4"):
            await callback.message.reply_video(f"{file}", caption=f"**Here Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}",
                                reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
            os.remove(f"{file}")
            break
        else:
            continue

    await msg.delete()
    active_list.remove(user_id)
