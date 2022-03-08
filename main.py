from importlib.resources import Package
import aiohttp
import argparse
import asyncio
import re
import time

from typing import List

import pyalpm
from pyalpm import Handle, DB

from config import handlers
from handler import Update

import betterlogging as logging

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

async def get_ftbfs_log(logurl: str):
    async with aiohttp.ClientSession(raise_for_status=True) as client:
        try:
            async with client.get(logurl) as response:
                return await response.text()
        except aiohttp.ClientResponseError as e:
            log.error('{}, message={!r}'.format(e.status, e.message))
        except Exception as e:
            log.exception(e)

async def get_ftbfs(data: str, *args):
    pat = re.compile(r'(?P<log_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{10}) \./\.status/logs/(?P<pkg_name>.*)/(?P<log_file>.*)')
    try:
        with open('db/ftbfs.log', 'r') as f:
            last_log = f.read().strip()
    except FileNotFoundError:
        last_log = ''

    update_time = last_log
    result = []
    if not data:
        log.warning('No FTBFS log found')
        return result
    for line in data.split('\n'):
        if m := pat.match(line):
            log_time, pkg_name, log_file = m.groups()
            if log_time > last_log:
                update_time = max(update_time, log_time)
                ts = int(time.mktime(time.strptime(log_time[:26], "%Y-%m-%d %H:%M:%S.%f")))
                should_update = True
                for db in args:
                    if pkg := db.get_pkg(pkg_name):
                        builddate = pkg.builddate
                        log.debug(f'{pkg_name} fail at: {ts}')
                        log.debug(f"{pkg_name} build at: {builddate}")
                        if ts < builddate:
                            log.warn(f'Ignore {pkg_name} fail at {log_time}')
                            should_update = False
                            break
                if should_update:
                    msg = f'FTBFS: {pkg_name} {log_file}'
                    result.append(Update(pkg_name, 'failed', None, None, None, None, msg))
                    log.info(msg)
    with open('db/ftbfs.log', 'w') as f:
        f.write(update_time)

    return result

async def run(baseurl, logurl, *args):
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

        update += await get_ftbfs(await get_ftbfs_log(logurl), *args)

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
    parser.add_argument(
        '--logurl',
        help="Set the FTBFS Log URL.",
        default="https://archriscv.felixc.at/.status/latestlogs.txt"
    )

    args = parser.parse_args()
    logging.basic_colorized_config(level=args.loglevel)
    baseurl = args.baseurl
    logurl = args.logurl
    handle = Handle('.', 'db')
    core: DB = handle.register_syncdb('core', pyalpm.SIG_DATABASE_OPTIONAL)
    extra: DB = handle.register_syncdb('extra', pyalpm.SIG_DATABASE_OPTIONAL)
    community: DB = handle.register_syncdb('community', pyalpm.SIG_DATABASE_OPTIONAL)

    for handler, kwargs in handlers.items():
        add_handler(handler, **kwargs)

    asyncio.run(run(baseurl, logurl, core, extra, community))


if __name__ == '__main__':
    main()
