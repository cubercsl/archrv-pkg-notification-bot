import asyncio

from typing import List

import aiohttp
import betterlogging as logging

from handler import Handler, Update

log = logging.getLogger(__name__)


class ArchRVBotHandler(Handler):
    status_map = {
        'update': 'ftbfs',
        'new': 'leaf'
    }

    def __init__(self, baseurl, token):
        self.baseurl = baseurl
        self.token = token

    async def _process_one(self, client: aiohttp.ClientSession, pkg_name: str, status: str):
        try:
            url = f'{self.baseurl}/delete/{pkg_name}/{status}'
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
        for update in updates:
            status = self.status_map.get(update.update_type)
            if status is None:
                continue
            msgs.append((update.pkg_name, status))
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, *msg) for msg in msgs])
