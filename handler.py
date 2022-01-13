from typing import List


class Update(object):
    def __init__(self, pkg_name, update_type=None, repo=None,
                 old_version=None, new_version=None, arch=None, msg=None):
        self.pkg_name = pkg_name
        self.update_type = update_type
        self.repo = repo
        self.old_version = old_version
        self.new_version = new_version
        self.arch = arch
        self.msg = msg


class Handler(object):
    async def process(self, data: List[Update]):
        pass
