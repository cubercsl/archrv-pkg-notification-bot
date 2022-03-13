import asyncio

from typing import List

import aiohttp
import betterlogging as logging

from handler import Handler, Update

log = logging.getLogger(__name__)


class ArchRVBotHandler(Handler):
    status_map = {
        'update': ('delete', 'ftbfs'),
        'new': ('delete','leaf'),
        'failed': ('add', 'ftbfs'),
    }

    def __init__(self, baseurl, token):
        self.baseurl = baseurl
        self.token = token

    async def _process_one(self, client: aiohttp.ClientSession, pkgbase: str, action: str, status: str):
        try:
            url = f'{self.baseurl}/{action}/{pkgbase}/{status}'
            async with client.get(url=url, params=dict(
                token=self.token
            )) as response:
                data = await response.text()
                log.info(data)
        except aiohttp.ClientResponseError as e:
            log.error('{}, message={!r}'.format(e.status, e.message))
        except Exception as e:
            log.exception(e)

    async def process(self, updates: List[Update]):
        log.info('send to archrv...')
        msgs = []
        updated_pkgbase = set()
        for update in updates:
            action_status = self.status_map.get(update.update_type)
            if (update.pkgbase, update.update_type) in updated_pkgbase:
                continue
            if action_status is None: 
                continue
            updated_pkgbase.add((update.pkgbase, update.update_type))
            action, status = action_status
            msgs.append((update.pkgbase, action, status))
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, *msg) for msg in msgs])
