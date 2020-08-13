__all__ = [
    "TestLog"
]

from collections import (
    defaultdict,
    deque,
)
from os import (
    linesep as os_linesep,
)
from time import (
    gmtime,
    strftime,
    time,
)


def default_timestamp_formatter(ts):
    return strftime("%H:%M:%S", gmtime(ts)) + ".%03f" % (ts % 1.0)

class TestLog(object):

    def __init__(self):
        self._runner2log = defaultdict(deque)

    def log(self, runner, dump, timestamp = None):
        if timestamp is None:
            timestamp = time()
        self._runner2log[runner].append((timestamp, dump))

    def iter_lines(self, runner,
        with_time = True,
        timestamp_base = 0.0,
        timestamp_formatter = default_timestamp_formatter,
    ):
        log = self._runner2log[runner]

        for ts, dump in log:
            if with_time:
                rts = ts - timestamp_base
                prefix = timestamp_formatter(rts) + ": "
            else:
                prefix = ""

            lter = iter(str(dump).splitlines(False))

            try:
                first_line = next(lter)
            except StopIteration:
                continue

            yield prefix + first_line

            space_prefix = " " * len(prefix)

            for l in lter:
                yield space_prefix + l

    def log_lines(self, runner, **iter_lines_kw):
        return list(self.iter_lines(runner, **iter_lines_kw))

    def joined_lines(self, runner, linesep = os_linesep, **iter_lines_kw):
        return linesep.join(self.log_lines(runner, **iter_lines_kw)) + linesep

    def to_file(self, runner, file_name, **kw):
        text = self.joined_lines(runner, **kw)
        with open(file_name, "w") as f:
            f.write(text)

    def iter_runners(self):
        return iter(self._runner2log)
