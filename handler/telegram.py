import asyncio
import html
import itertools

from typing import List

import aiohttp
import betterlogging as logging

from handler import Handler, Update

log = logging.getLogger(__name__)


class TelegramBotHandler(Handler):

    def __init__(self, bot_token: str, chat_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        self.chat_id = chat_id

    async def _process_one(self, client: aiohttp.ClientSession, group: List[Update], chat_id: str):
        lines = ['<b>Arch Linux RISC-V: Recent package updates</b>']
        for item in group:
            if item.old_version:
                lines.append(html.escape(f'{item.pkgname} {item.old_version} -> {item.new_version}'))
            else:
                lines.append(html.escape(f'{item.pkgname} {item.new_version}'))

        msg = '\n'.join(lines)

        if self.dry_run:
            log.debug(f'{chat_id} {msg}')
            return

        async with client.get(self.url, params=dict(
            chat_id=chat_id,
            text=msg,
            parse_mode='HTML'
        )) as response:
            try:
                data = await response.json()
                log.info(data)
            except aiohttp.ClientResponseError as e:
                log.error('{}, message={!r}'.format(e.status, e.message))
            except Exception as e:
                log.exception(e)

    async def process(self, updates: List[Update]):
        log.info('send to telegram...')
        # Do not post FTBFS updates to telegram
        updates = list(filter(lambda item: item.update_type in ('update', 'new') ,updates))
        total = len(updates)
        groups = [updates[idx:idx + 10] for idx in range(0, total, 10)]
        chat_id = self.chat_id.split(',') if not self.dry_run else [0]
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, group, _chat_id) for group, _chat_id in
                                   itertools.product(groups, chat_id)])
