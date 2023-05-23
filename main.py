import aiohttp
import argparse
import asyncio
import re
import sys
import time

from typing import List

import pyalpm
from pyalpm import Handle, DB

from config import handlers, push
from handler import Update

import betterlogging as logging

log: logging.BetterLogger = logging.getLogger(__name__)
update_handler = []
provide_pattern = re.compile(r'^(?P<name>[0-9a-z@._+\-]+)(?P<version>.*)$')


def add_handler(handler, dry_run, *args, **kwargs):
    if dry_run or all(args) and all(kwargs.values()):
        update_handler.append(handler(dry_run=dry_run, *args, **kwargs))
    else:
        log.warning(f'ignore handler: {handler}')


def get_packages(packages: list[pyalpm.Package]):
    return dict((pkg.name, (pkg.version, pkg.arch, pkg.base, pkg.provides)) for pkg in packages)


def get_update(before, after, pkgnames):
    
    def _get_provides(provides):
        result = []
        for provide in provides:
            if match := provide_pattern.match(provide):
                name = match.group('name')
                if name not in pkgnames:
                    result.append(name)
        return result

    result = []
    for name, value in after.items():
        new_version, new_arch, pkgbase, provides = value
        if provides: 
            provides = _get_provides(provides)
        if name in before:
            old_version, *_ = before[name]
            if pyalpm.vercmp(new_version, old_version) > 0:
                msg = f'Update: {name} {old_version} -> {new_version} {new_arch}'
                result.append(Update(name, pkgbase, provides, 'update', old_version, new_version, new_arch, msg))
                log.info(msg)
        else:
            msg = f'New: {name} {new_version} {new_arch}'
            result.append(Update(name, pkgbase, provides, 'new', None, new_version, new_arch, msg))
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
    pat = re.compile(r'(?P<log_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{10}) \./\.status/logs/(?P<pkgbase>.*)/(?P<log_file>.*)')
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
            log_time, pkgbase, log_file = m.groups()
            if log_time > last_log:
                update_time = max(update_time, log_time)
                ts = int(time.mktime(time.strptime(log_time[:26], "%Y-%m-%d %H:%M:%S.%f")))
                should_update = True
                for db in args:
                    if pkg := db.get_pkg(pkgbase):
                        builddate = pkg.builddate
                        log.debug(f'{pkgbase} fail at: {ts}')
                        log.debug(f"{pkgbase} build at: {builddate}")
                        if ts < builddate:
                            log.warning(f'Ignore {pkgbase} fail at {log_time}')
                            should_update = False
                            break
                if should_update:
                    msg = f'FTBFS: {pkgbase} {log_file}'
                    # We should not send provides as ftbfs.
                    result.append(Update(pkgbase, pkgbase, list(), 'failed', None, None, None, msg))
                    log.info(msg)
    with open('db/ftbfs.log', 'w') as f:
        f.write(update_time)

    return result

async def run(baseurl, logurl, *args):
    for db in args:
        db.servers = [f"{baseurl}/{db.name}"]
    while True:
        asyncio.create_task(push.push(status='up', msg='Syncing...'))
        update = []
        before_sync = dict()
        after_sync = dict()
        for db in args[::-1]:
            log.debug(f'Syncing {db.name}...')
            before_sync.update(get_packages(db.pkgcache))

            try:
                db.update(False)
            except Exception as e:
                log.exception(e)
                await push.push(status='down', msg=f'Failed to sync {db.name}')
                sys.exit(0)

            after_sync.update(get_packages(db.pkgcache))

        update += get_update(before_sync, after_sync, after_sync.keys())

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
    parser.add_argument(
        '--dry-run',
        help='Run handlers without updating',
        action='store_true',
        default=False
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
        add_handler(handler, args.dry_run, **kwargs)
    if args.dry_run:
        push.dry_run = True

    asyncio.run(run(baseurl, logurl, core, extra, community))


if __name__ == '__main__':
    main()
