from pyrogram import Client, filters
import logging
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from config import Config, Txt
from helper.database import db
from .check_user_status import handle_user_status
from helper.utils import is_subscribed, force_sub

logger = logging.getLogger(__name__)


@Client.on_message(filters.private)
async def _(bot: Client, cmd: Message):

    if not await is_subscribed(bot, cmd):
        return await force_sub(bot, cmd)
    await handle_user_status(bot, cmd)
    await cmd.continue_propagation()


@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):

    if message.from_user.id in Config.BANNED_USERS:
        await message.reply_text("Sorry, You are banned.")
        return

    user = message.from_user
    button = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            '⛅ Uᴩᴅᴀᴛᴇꜱ', url='https://t.me/zenupdatess'),
        InlineKeyboardButton(
            '🌨️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/ZencontBot')
    ], [
        InlineKeyboardButton('👨‍💻 Aʙᴏᴜᴛ', callback_data='about'),
        InlineKeyboardButton('❗ Hᴇʟᴩ', callback_data='help')
    ],
        [
        InlineKeyboardButton("Search Porn Here",
                             switch_inline_query_current_chat="",)
    ]])
    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)


# ⚠️ Handling CallBack Query⚠️

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    if data == "start":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    '⛅ Uᴩᴅᴀᴛᴇꜱ', url='https://t.me/zenupdatess'),
                InlineKeyboardButton(
                    '🌨️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/ZencontBot')
            ], [
                InlineKeyboardButton('👨‍💻 Aʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('❗ Hᴇʟᴩ', callback_data='help')
            ],
                [
                InlineKeyboardButton("Search Porn Here",
                                     switch_inline_query_current_chat="",)
            ]])
        )

    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")
            ]])
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT.format(client.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data="close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data="start")
            ]])
        )

    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()
