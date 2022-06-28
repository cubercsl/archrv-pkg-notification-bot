import asyncio
import re

from typing import List

import aiohttp
import betterlogging as logging

from handler import Handler, Update

log: logging.BetterLogger = logging.getLogger(__name__)


class ArchRVBotHandler(Handler):

    provide_pattern = re.compile(r'^(?P<name>[0-9a-z@._+\-]+)(?P<version>.*)$')

    status_map = {
        'update': ('delete', 'ftbfs'),
        'new': ('delete','leaf'),
        'failed': ('add', 'ftbfs'),
    }

    def __init__(self, baseurl, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseurl = baseurl
        self.token = token

    async def _process_one(self, client: aiohttp.ClientSession, pkgbase: str, action: str, status: str):
        if self.dry_run:
            log.debug(f'{action} {status} {pkgbase}')
            return
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
        updated_item = set()
        for update in updates:
            action_status = self.status_map.get(update.update_type)
            if action_status is None:
                continue
            action, status = action_status
            if (update.pkgbase, update.update_type) not in updated_item:                
                updated_item.add((update.pkgbase, update.update_type))
                msgs.append((update.pkgbase, action, status))
            if (update.pkgname, update.update_type) not in updated_item:
                updated_item.add((update.pkgname, update.update_type))
                msgs.append((update.pkgname, action, status))
            
            for provide_item in update.provides:
                if match := self.provide_pattern.match(provide_item):
                    provide = match.group('name')
                    if (provide, update.update_type) not in updated_item:
                        updated_item.add((provide, update.update_type))
                        msgs.append((provide, action, status))

        async with aiohttp.ClientSession(raise_for_status=True) as client:
            await asyncio.gather(*[self._process_one(client, *msg) for msg in msgs])
