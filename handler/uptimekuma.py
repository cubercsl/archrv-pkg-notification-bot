import aiohttp

import betterlogging as logging

log: logging.BetterLogger = logging.getLogger(__name__)

class UptimeKumaPushHandler:
    def __init__(self, baseurl, token):
        self.baseurl = baseurl
        self.token = token
    
    async def push(self, status: str, msg: str):
        log.info(msg)
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            url = f'{self.baseurl}/api/push/{self.token}'
            await client.get(url=url, params=dict(
                status=status,
                msg=msg,
            ))
        