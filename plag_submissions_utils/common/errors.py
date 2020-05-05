#!/usr/bin/env python
# coding: utf-8


class ErrSeverity(object):
    LOW = 0
    NORM = 1
    HIGH = 2

class Error(object):
    def __init__(self, msg, sev = ErrSeverity.NORM,
                 extra = None):
        self.msg = msg
        self.sev   = sev
        self.extra = extra if extra is not None else []

    def _get_extra_str(self):
        if self.extra:
            return "\n" + '\n'.join(self.extra)
        return ''

    def __str__(self):
        main = "!" * self.sev + " " + self.msg
        main += self._get_extra_str()
        return main

class ChunkError(Error):
    def __init__(self, msg, chunk_num, sev = ErrSeverity.NORM,
                 extra = None):
        super(ChunkError, self).__init__(msg, sev, extra)
        self.chunk_num = chunk_num
    def __str__(self):
        pref = "!" * self.sev
        return  "%s Предложение #%d: %s" %(pref, self.chunk_num, self.msg) + \
            self._get_extra_str()
