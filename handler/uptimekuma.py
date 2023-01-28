import aiohttp

import betterlogging as logging

from handler import Handler

log: logging.BetterLogger = logging.getLogger(__name__)

class UptimeKumaPushHandler(Handler):
    def __init__(self, baseurl, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseurl = baseurl
        self.token = token
    
    async def push(self, status: str, msg: str):
        if self.dry_run:
            log.debug(f'push {status} {msg}')
            return
        log.info(msg)
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            url = f'{self.baseurl}/api/push/{self.token}'
            await client.get(url=url, params=dict(
                status=status,
                msg=msg,
            ))
        