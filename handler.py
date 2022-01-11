from typing import List


class Update (object):
    def __init__(self, pkg_name, update_type=None, msg=None):
        self.pkg_name = pkg_name
        self.update_type = update_type
        self.msg = msg


class Handler (object):
    async def process(self, data: List[Update]):
        pass
