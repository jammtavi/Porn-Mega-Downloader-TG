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


active_list = []
download_queue = asyncio.Queue()


def link_fil(filter, client, update):
    if "https://www.pornhub" in update.text:
        return True
    else:
        return False


link_filter = filters.create(link_fil, name="link_filter")


async def process_queue(client):
    while True:
        message = await download_queue.get()

        user_id = message.from_user.id
        if user_id not in active_list:
            active_list.append(user_id)

        link = message.text
        done = await Download_Porn_Video(client, message, link)

        if done:
            active_list.remove(user_id)

        download_queue.task_done()

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

    await download_queue.put(message)


@Client.on_message(filters.command("cc"))
async def download_video(client, message: Message):
    files = os.listdir("downloads")
    await message.reply(files)


# Start the queue processing task
asyncio.ensure_future(process_queue(Client))
