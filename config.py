import os

from handler.archrvbot import ArchRVBotHandler
from handler.telegram import TelegramBotHandler, TelegramBotErrorNotify

handlers = {
    ArchRVBotHandler: dict(
        baseurl=os.getenv('archrv__baseurl'),
        token=os.getenv('archrv__token')
    ),
    TelegramBotHandler: dict(
        chat_id=os.getenv('telegram__chat_id'),
        bot_token=os.getenv('telegram__bot_token')
    )
}

notify = TelegramBotErrorNotify(chat_id=os.getenv('telegram_notify__chat_id'), bot_token=os.getenv('telegram_notify__bot_token'))
