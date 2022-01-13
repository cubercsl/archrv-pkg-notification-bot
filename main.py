import argparse
import asyncio
import logging

from typing import List

import pyalpm
from pyalpm import Handle, DB

from config import handlers
from handler import Update


log = logging.getLogger(__name__)

update_handler = []


def add_handler(handler, *args, **kwargs):
    if all(args) and all(kwargs.values()):
        update_handler.append(handler(*args, **kwargs))
    else:
        log.warning(f'ignore handler: {handler}')


def get_packages(packages: list[pyalpm.Package]):
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


async def run(baseurl, *args):
    for db in args:
        db.servers = [f"{baseurl}/{db.name}"]

    while True:
        update = []
        for db in args:
            log.info(f'Syncing {db.name}...')
            before_sync = get_packages(db.pkgcache)
            db.update(False)
            after_sync = get_packages(db.pkgcache)
            update += get_update(db.name, before_sync, after_sync)

        asyncio.create_task(handle_update(update))
        await asyncio.sleep(60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    parser.add_argument(
        '--baseurl',
        help="Set Repo baseURL",
        default="https://archriscv.felixc.at/repo"
    )

    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s - [%(levelname)s] - %(message)s',
                        level=args.loglevel)

    baseurl = args.baseurl
    handle = Handle('.', 'db')
    core: DB = handle.register_syncdb('core', pyalpm.SIG_DATABASE_OPTIONAL)
    extra: DB = handle.register_syncdb('extra', pyalpm.SIG_DATABASE_OPTIONAL)
    community: DB = handle.register_syncdb('community', pyalpm.SIG_DATABASE_OPTIONAL)

    for handler, kwargs in handlers.items():
        add_handler(handler, **kwargs)

    asyncio.run(run(baseurl, core, extra, community))


if __name__ == '__main__':
    main()
