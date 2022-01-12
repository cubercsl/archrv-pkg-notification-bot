import asyncio
import logging
import os

from typing import List

import pyalpm
from pyalpm import Handle, DB

from handler import Update

from archrvbot import ArchRVBotHandler
from telegram import TelegramBotHandler

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(format='%(asctime)s - %(message)s', level=LOGLEVEL)
log = logging.getLogger(__name__)

update_handler = []


def add_handler(className, *args):
    if all(args):
        update_handler.append(className(*args))
    else:
        log.warning(f'ignore handler: {className}')


def get_packages(packages: List[pyalpm.Package]):
    return dict((pkg.name, (pkg.version, pkg.arch)) for pkg in packages)


def get_update(db_name, before, after):
    result = []
    for name, value in after.items():
        new_version, new_arch = value
        if name in before:
            old_version, old_arch = before[name]
            if pyalpm.vercmp(new_version, old_version) > 0:
                msg = f'Update: {db_name} {name} {old_version} -> {new_version} {new_arch}'
                result.append(Update(name, 'update', db_name, old_version, new_version, new_arch, msg))
                log.info(msg)
        else:
            msg = f'New: {db_name} {name} {new_version} {new_arch}'
            result.append(Update(name, 'new', db_name, None, new_version, new_arch, msg))
            log.info(msg)
    return result


async def handle_update(data: List[Update]):
    if num := len(data):
        log.info(f'{num} update(s)')
    else:
        log.debug(f'No update')
        return
    for handler in update_handler:
        asyncio.create_task(handler.process(data))


async def main():
    baseurl = 'https://archriscv.felixc.at/repo'
    handle = Handle('.', 'db')
    core: DB = handle.register_syncdb('core', pyalpm.SIG_DATABASE_OPTIONAL)
    extra: DB = handle.register_syncdb('extra', pyalpm.SIG_DATABASE_OPTIONAL)
    community: DB = handle.register_syncdb('community', pyalpm.SIG_DATABASE_OPTIONAL)

    for db in (core, extra, community):
        db.servers = [f"{baseurl}/{db.name}"]

    while True:
        update = []
        for db in (core, extra, community):
            log.debug(f'Syncing {db.name}...')
            before_sync = get_packages(db.pkgcache)
            db.update(False)
            after_sync = get_packages(db.pkgcache)
            update += get_update(db.name, before_sync, after_sync)

        asyncio.create_task(handle_update(update))
        await asyncio.sleep(60)


if __name__ == '__main__':

    plctbot_url, plctbot_token = os.getenv('plctbot_url'), os.getenv('plctbot_token')
    add_handler(ArchRVBotHandler, plctbot_url, plctbot_token)

    bot_token, chat_id = os.getenv('bot_token'), os.getenv('chat_id')
    add_handler(TelegramBotHandler, bot_token, chat_id)

    asyncio.run(main())
