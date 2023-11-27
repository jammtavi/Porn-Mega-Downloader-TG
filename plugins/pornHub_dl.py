import asyncio
import os
import sys

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
from helper.utils import download_progress_hook, Download_Porn_Video


if os.path.exists("downloads"):
    print("Download Path Exist")
else:
    print("Download Path Created")

btn1 = InlineKeyboardButton(
    "Search Here", switch_inline_query_current_chat="",)
btn2 = InlineKeyboardButton("Go Inline", switch_inline_query="")

User_Queue = {}
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
async def options(client, message: Message):
    try:
        if not await is_subscribed(client, message):
            return await force_sub(client, message)

        await message.reply("What would like to do?", reply_to_message_id=message.id,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(text="🔻 Download 🔻", callback_data= f"d_{message.text}"), InlineKeyboardButton(text="➕ Add Multiple Links ➕", callback_data=f"m_{message.text}")],
                                [InlineKeyboardButton(text="📺 Watch Video 📺  ",url=message.text)]
                            ])
                            )
    except Exception as e:
        print(e)

@Client.on_callback_query(filters.regex("^d"))
async def single_download(client, callback: CallbackQuery):
    url = callback.data.split("_", 1)[1]
    msg = await callback.message.edit(f"**Link:-** {url}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True)
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


@Client.on_callback_query(filters.regex("^m"))
async def multiple_download(client, callback: CallbackQuery):
    try:
        global User_Queue
        user_id = callback.from_user.id

        if user_id not in User_Queue:
            User_Queue.update({user_id: [callback.data.split('_', 1)[1]]})
            while True:
                link = await client.ask(chat_id=user_id, text="🔗Send Link to add it to queue 🔗\n\nUse /done when you're done adding links to queue.", filters=filters.text)

                if str(link.text).startswith("https://www.pornhub"):
                    User_Queue[user_id].append(link.text)
                    await callback.message.reply_text("Successfully Added To Queue ✅", reply_to_message_id=link.id)

                elif link.text == "/done":
                    user = User_Queue[user_id]
                    links = ""
                    for idx, link in enumerate(user):
                        links += f"{(idx+1)}. {link}\n"

                    await callback.message.reply_text(f"👤 <code>{callback.message.from_user.first_name}</code>\n\n <code>{links}</code>")
                    break

                else:
                    await callback.answer("Please Send Valid Link !")
                    continue

        await callback.message.reply_text("Downloading Started ✅\n\nPlease have patience while it's downloading it may take sometimes...")

        number = 0
        while True:
            try:
                link = User_Queue[user_id][number]
                msg = await callback.message.reply_text(f"**Link:-** {link}\n\nDownloading... Please Have Patience\n 𝙇𝙤𝙖𝙙𝙞𝙣𝙜...", disable_web_page_preview=True)

                ydl_opts = {
                      "progress_hooks": [lambda d: download_progress_hook(d, msg, client)],

                 }

                 with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                   
                   try:
                     
                     await run_async(ydl.download, [link])
                   except DownloadError:
                     await msg.edit(f"**Link:-** {link}\n\n☹️ Sorry, There was a problem with that particular video")
                     return

                 for file in os.listdir('.'):
                   
                   if file.endswith(".mp4"):
                     
                     await client.send_video(user_id, f"{file}", caption=f"**File Name:- <code>{file}</code>\n\nHere Is your Requested Video**\nPowered By - @{Config.BOT_USERNAME}",reply_markup=InlineKeyboardMarkup([[btn1, btn2]]))
                     os.remove(f"{file}")
                     break
                   else:
                     continue

                 await msg.delete()
            except Exception as e:
                print(e)
                break
            number+=1
            continue

        # clean up the queue
        number= 0
        print("All links Downloaded Successfully ✅")
        await client.send_message(user_id, f"**List:- ** <code> {User_Queue[user_id]} </code>\n\n🎯 All links Downloaded Successfully ✅")
        User_Queue.pop(user_id)
      
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
