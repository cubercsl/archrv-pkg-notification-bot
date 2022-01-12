import asyncio
import logging

from typing import List

import aiohttp

from handler import Handler, Update

log = logging.getLogger(__name__)


class TelegramBotHandler(Handler):

    def __init__(self, token, chat_id):
        self.url = f'https://api.telegram.org/bot{token}/sendMessage'
        self.chat_id = chat_id

    async def _process_one(self, client, msg):
        try:
            async with client.get(self.url, params=dict(
                chat_id=self.chat_id,
                text=msg
            )) as response:
                data = await response.text()
                log.debug(data)
        except Exception as e:
            log.error(e)

    async def process(self, updates: List[Update]):
        log.debug('send to telegram...')
        total = len(updates)

        msgs = []
        for idx in range(0, total, 10):
            msgs.append('\n'.join(update.msg for update in updates[idx:idx + 10]))

        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, msg) for msg in msgs])
