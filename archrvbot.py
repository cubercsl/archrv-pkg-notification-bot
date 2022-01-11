import logging

from typing import List

import aiohttp

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

    async def process(self, updates: List[Update]):
        log.debug('send to archrv-pkg...')
        for update in updates:
            status = self.status_map.get(update.update_type)
            if status is None:
                continue
            url = f'{self.baseurl}/delete/{update.pkg_name}/{status}'
            try:
                log.debug(f'GET {url}')
                data = await aiohttp.ClientSession.get(url=url, params=dict(
                    token=self.token
                ))
                log.debug(data)
            except Exception as e:
                log.error(e)
