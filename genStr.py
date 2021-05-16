import asyncio
import os
import time
from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired, UserNotParticipant
)
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid
from creds import Credentials

API_TEXT = """👋🏻 **Hi {}**,

I'm **String Session Generator** \nI Can Generate Pyrogram's String Session Of Your Telegram Account.

Now Send Your `API_ID` Same As `APP_ID` To Start Generating Session.

Get API_ID from https://my.telegram.org"""
HASH_TEXT = "Now Send Your `API_HASH`.\n\nGet API_HASH From https://my.telegram.org\n\nPress /cancel to Cancel Task."
PHONE_NUMBER_TEXT = (
    "Now Send Your Telegram Account's Phone Number in International Format. \n"
    "Including Country Code. Example: **+14154566376**\n\n"
    "Press /cancel to Cancel Task."
)


UPDATES_CHANNEL = os.environ.get('UPDATES_CHANNEL', 'AsmSafone')

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    if msg.chat.id in Credentials.BANNED_USERS:
        await bot.send_message(
            chat_id=msg.chat.id,
            text="You are Banned. Contact My [Support Group](https://t.me/safothebot)",
            reply_to_message_id=msg.message_id
        )
        return
    ## Doing Force Sub 🤣
    update_channel = UPDATES_CHANNEL
    if update_channel:
        try:
            user = await bot.get_chat_member(update_channel, msg.chat.id)
            if user.status == "kicked":
               await bot.send_message(
                   chat_id=msg.chat.id,
                   text="Sorry Sir, You are Banned. Contact My [Support Group](https://t.me/safothebot).",
                   parse_mode="markdown",
                   disable_web_page_preview=True
               )
               return
        except UserNotParticipant:
            await bot.send_message(
                chat_id=msg.chat.id,
                text="**Please Join My Updates Channel To Use Me!**",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🤖 Join Updates Channel 🤖", url=f"https://t.me/{update_channel}")
                        ]
                    ]
                ),
                parse_mode="markdown"
            )
            return
        except Exception:
            await bot.send_message(
                chat_id=msg.chat.id,
                text="**Something Went Wrong. Contact My [Support Group](https://t.me/safothebot).**",
                parse_mode="markdown",
                disable_web_page_preview=True
            )
            return

    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` is Invalid.\nPress /start to Start Again!")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`API_HASH` is Invalid.\nPress /start to Start Again!")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`Is "{phone}" Correct? (y/n):` \n\nSend: `y` (If Yes)\nSend: `n` (If No)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nPress /start to Start Again!")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"You Have Floodwait of {e.x} Seconds")
        return
    except ApiIdInvalid:
        await msg.reply("API ID and API Hash are Invalid.\n\nPress /start to Start Again!")
        return
    except PhoneNumberInvalid:
        await msg.reply("Your Phone Number is Invalid.\n\nPress /start to Start Again!")
        return
    try:
        otp = await bot.ask(
            chat.id, ("An OTP is sent to your phone number, "
                      "Please enter OTP in `1 2 3 4 5` format. __(Space between each numbers!)__ \n\n"
                      "If Bot not sending OTP then try /restart and Start Task again with /start command to Bot.\n"
                      "Press /cancel to Cancel."), timeout=300)

    except TimeoutError:
        await msg.reply("Time Limit Reached of 5 Min.\nPress /start to Start Again!")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("Invalid Code.\n\nPress /start to Start Again!")
        return
    except PhoneCodeExpired:
        await msg.reply("Code is Expired.\n\nPress /start to Start Again!")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "Your Account Have Two-Step Verification.\nPlease Enter Your Password.\n\nPress /cancel to Cancel.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Time Limit Reached of 5 Min.\n\nPress /start to Start Again!`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION \n\n```{session_string}``` \n\nBy [String Session Generator](http://t.me/genStr_robot) 🤖\nMade with ❤️ By @AsmSafone! 👑")
        await client.disconnect()
        text = "String Session is Successfully ✅ Generated.\nClick On Below Button To Get."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="SHOW STRING SESSION", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("Restarted Bot! ✅")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hi {msg.from_user.mention}, \nThis is Pyrogram Session String Generator Bot. \
It Can Generate `STRING_SESSION` Of Your Telegram Account For Your UserBot.

It Needs `API_ID`, `API_HASH`, Phone Number & One Time Verification Code. \
Which Will Be Sent to Your Phone Number or Telegram App.
You Have to Put **OTP** in `1 2 3 4 5` This Format. __(Space between each numbers)__

**NOTE:** If Bot Not Sending OTP to Your Phone Number than send /restart Command & Again Send /start to Start Your Process. 

Must Join Channel for Bot Updates !!
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('CHANNEL', url='https://t.me/AsmSafone'),
                InlineKeyboardButton('SUPPORT', url='https://t.me/Safothebot')
            ],
            [
                InlineKeyboardButton('DEVELOPER', url='https://t.me/I_Am_Only_One_1'),
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Process Cancelled! ✅")
        return True
    return False

if __name__ == "__main__":
    bot.run()
