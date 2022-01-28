import os

from handler.archrvbot import ArchRVBotHandler
from handler.telegram import TelegramBotHandler

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
