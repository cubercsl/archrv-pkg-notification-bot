import logging

from typing import List

import aiohttp

from handler import Handler, Update

log = logging.getLogger(__name__)


class TelegramBotHandler(Handler):
    baseurl = 'https://api.telegram.org/bot'

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    async def process(self, updates: List[Update]):
        log.debug('send to telegram...')
        total = len(updates)
        url = f'{self.baseurl}{self.token}/sendMessage'
        for idx in range(0, total, 10):
            msg = '\n'.join(update.msg for update in updates[idx:idx + 10])
            try:
                data = await aiohttp.ClientSession().get(url, params=dict(
                    chat_id=self.chat_id,
                    text=msg
                ))
                log.debug(data)
            except Exception as e:
                log.error(e)
