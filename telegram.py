import asyncio
import html
import itertools
import logging

from typing import List

import aiohttp

from handler import Handler, Update

log = logging.getLogger(__name__)


class TelegramBotHandler(Handler):

    def __init__(self, bot_token: str, chat_id: str):
        self.url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        self.chat_id = chat_id

    async def _process_one(self, client: aiohttp.ClientSession, group: List[Update], chat_id: str):
        lines = ['<b>Arch Linux RISC-V: Resent package updates</b>']
        for item in group:
            if item.old_version:
                lines.append(html.escape(f'{item.pkg_name} {item.old_version} -> {item.new_version}'))
            else:
                lines.append(html.escape(f'{item.pkg_name} {item.new_version}'))

        msg = '\n'.join(lines)

        async with client.get(self.url, params=dict(
            chat_id=chat_id,
            text=msg,
            parse_mode='HTML'
        )) as response:
            try:
                data = await response.text()
                log.debug(data)
            except aiohttp.ClientResponseError as e:
                log.error('{}, message={!r}'.format(e.status, e.message))
            except Exception as e:
                log.error(e)

    async def process(self, updates: List[Update]):
        log.info('send to telegram...')
        total = len(updates)
        groups = [updates[idx:idx + 10] for idx in range(0, total, 10)]
        chat_id = self.chat_id.split(',')
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, group, _chat_id) for group, _chat_id in
                                   itertools.product(groups, chat_id)])
