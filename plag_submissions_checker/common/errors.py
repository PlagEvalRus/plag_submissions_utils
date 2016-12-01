#!/usr/bin/env python
# coding: utf-8


class ErrSeverity(object):
    LOW = 0
    NORM = 1
    HIGH = 2

class Error(object):
    def __init__(self, msg, sev = ErrSeverity.NORM):
        self.msg = msg
        self.sev = sev
    def __str__(self):
        return "!" * self.sev + self.msg

class ChunkError(Error):
    def __init__(self, msg, chunk_num, sev = ErrSeverity.NORM):
        super(ChunkError, self).__init__(msg, sev)
        self.chunk_num = chunk_num
    def __str__(self):
        pref = "!" * self.sev
        return  "%s Предложение #%d: %s" %(pref, self.chunk_num, self.msg)
