import os

from handler.archrvbot import ArchRVBotHandler
from handler.telegram import TelegramBotHandler, TelegramBotErrorNotify
from handler.uptimekuma import UptimeKumaPushHandler
handlers = {
    ArchRVBotHandler: dict(
        baseurl=os.getenv('archrv__baseurl'),
        token=os.getenv('archrv__token'),
        error_handler=TelegramBotErrorNotify(
            chat_id=os.getenv('telegram_notify__chat_id'),
            bot_token=os.getenv('telegram_notify__bot_token')
        )
    ),
    TelegramBotHandler: dict(
        chat_id=os.getenv('telegram__chat_id'),
        bot_token=os.getenv('telegram__bot_token')
    )
}

push = UptimeKumaPushHandler(baseurl=os.getenv('uptimekuma__baseurl'), token=os.getenv('uptimekuma__token'))
