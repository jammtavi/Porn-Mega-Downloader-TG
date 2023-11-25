import asyncio
import os
import sys

from pornhub_api import PornhubApi
from pornhub_api.backends.aiohttp import AioHttpBackend
from pyrogram import Client, filters
from pyrogram.errors.exceptions import UserNotParticipant
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, InlineQuery,
                            InlineQueryResultArticle, InputTextMessageContent,
                            Message)
from helper.utils import Download_Porn_Video
from helper.utils import force_sub, is_subscribed
from config import Config
from helper.utils import download_progress_hook


if os.path.exists("downloads"):
    print("Download Path Exist")
else:
    print("Download Path Created")


User_Queue = {}


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
                InlineKeyboardButton(
                    "Search Here", switch_inline_query_current_chat="",)
            ]]),
        ))

    await InlineQuery.answer(results,
                             switch_pm_text="Search Results",
                             switch_pm_parameter="start")


@Client.on_message(link_filter)
async def _download_video(client, message: Message):
    global User_Queue
    user_id = message.from_user.id

    if not User_Queue:
        User_Queue.update({user_id: [message.text]})

    elif user_id in User_Queue:
        User_Queue[user_id].append(message.text)
        return

    else:
        User_Queue.update({user_id: [message.text]})

    for link in User_Queue[user_id]:
        if link:
            done = await Download_Porn_Video(client, message, link)
            if done:
                continue
        else:
          break

    print(User_Queue)
    User_Queue.pop(user_id)
    print(User_Queue)


@Client.on_message(filters.command("cc"))
async def download_video(client, message: Message):
    try:
        if message.from_user.id in User_Queue:

            user = User_Queue[message.from_user.id]
            print(user)
            links = ""
            for idx, link in enumerate(user):
                links += f"{(idx+1)}. {link}\n"

            await message.reply_text(f"{user}\n\n {links}")
        else:
            s = await message.reply_text("**NO PROCESS FOUND !")
            await asyncio.sleep(5)
            await s.delete()
    except Exception as e:
        await message.reply_text(f"{e}\n\n\n **Error !**")
