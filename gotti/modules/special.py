from io import BytesIO
import html
import requests
import random
from time import sleep
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot, MessageEntity
from telegram.error import BadRequest
from telegram import ParseMode
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown
from html import escape
from gotti.modules.helper_funcs.chat_status import is_user_ban_protected, bot_admin, user_admin
import gotti.modules.sql.users_sql as sql
from gotti import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, LOGGER
from gotti.modules.helper_funcs.filters import CustomFilters
from gotti.modules.disable import DisableAbleCommandHandler

USERS_GROUP = 4


def escape_html(word):
    return escape(word)


@run_async
def quickscope(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("You don't seem to be referring to a chat/user")
    try:
        bot.kick_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Attempted banning " + to_kick + " from" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def quickunban(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("You don't seem to be referring to a chat/user")
    try:
        bot.unban_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Attempted unbanning " + to_kick + " from" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def banall(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[0])
        all_mems = sql.get_chat_members(chat_id)
    else:
        chat_id = str(update.effective_chat.id)
        all_mems = sql.get_chat_members(chat_id)
    for mems in all_mems:
        try:
            bot.kick_chat_member(chat_id, mems.user)
            update.effective_message.reply_text("Tried banning " + str(mems.user))
            sleep(0.1)
        except BadRequest as excp:
            update.effective_message.reply_text(excp.message + " " + str(mems.user))
            continue


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text("Couldn't send the message. Perhaps I'm not part of that group?")



@bot_admin
def leavechat(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        update.effective_message.reply_text("You do not seem to be referring to a chat!")
    try:
        chat = bot.getChat(chat_id)
        titlechat = bot.get_chat(chat_id).title
        bot.sendMessage(chat_id, "`I Go Away!`")
        bot.leaveChat(chat_id)
        update.effective_message.reply_text("I left group {}".format(titlechat))

    except BadRequest as excp:
        if excp.message == "Chat not found":
            update.effective_message.reply_text("It looks like I've been kicked out of the group :p")
        else:
            return

@run_async
def slist(bot: Bot, update: Update):
    message = update.effective_message
    text1 = "My sudo users are:"
    text2 = "My support users are:"
    for user_id in SUDO_USERS:
        try:
            user = bot.get_chat(user_id)
            name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
            if user.username:
                name = escape_html("@" + user.username)
            text1 += "\n - `{}`".format(name)
        except BadRequest as excp:
            if excp.message == 'Chat not found':
                text1 += "\n - ({}) - not found".format(user_id)
    for user_id in SUPPORT_USERS:
        try:
            user = bot.get_chat(user_id)
            name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
            if user.username:
                name = escape_html("@" + user.username)
            text2 += "\n - `{}`".format(name)
        except BadRequest as excp:
            if excp.message == 'Chat not found':
                text2 += "\n - ({}) - not found".format(user_id)
    message.reply_text(text1 + "\n", parse_mode=ParseMode.MARKDOWN)
    message.reply_text(text2 + "\n", parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)

MESSAGES = (
    "Happy birthday ",
    "Heppi burfdey ",
    "Hep burf ",
    "Happy day of birthing ",
    "Sadn't deathn't-day ",
    "Oof, you were born today ",
)

#Burfday module from Lynda Robot
@run_async
@user_admin
def birthday(bot: Bot, update: Update, args: List[str]):
    if args:
        username = str(",".join(args))
    bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
    for i in range(5):
        bdaymessage = random.choice(MESSAGES)
        update.effective_message.reply_text(bdaymessage + username)

__mod_name__ = "SPECIAL"

SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=Filters.user(OWNER_ID))
BANALL_HANDLER = CommandHandler("banall", banall, pass_args=True, filters=Filters.user(OWNER_ID))
QUICKSCOPE_HANDLER = CommandHandler("quickscope", quickscope, pass_args=True, filters=CustomFilters.sudo_filter)
QUICKUNBAN_HANDLER = CommandHandler("quickunban", quickunban, pass_args=True, filters=CustomFilters.sudo_filter)

LEAVECHAT_HANDLER = CommandHandler("leavechat", leavechat, pass_args=True, filters=Filters.user(OWNER_ID))
SLIST_HANDLER = CommandHandler("slist", slist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))
BIRTHDAY_HANDLER = DisableAbleCommandHandler("birthday", birthday, pass_args=True, filters=Filters.group)

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
dispatcher.add_handler(QUICKSCOPE_HANDLER)
dispatcher.add_handler(QUICKUNBAN_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(SLIST_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(BIRTHDAY_HANDLER)
