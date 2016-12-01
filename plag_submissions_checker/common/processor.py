#!/usr/bin/env python
# coding: utf-8

import logging
import os
import os.path as fs
import re

from .errors import ErrSeverity
from .errors import Error
from .stat import StatCollector
from .source_doc import SourceDoc
from . import source_doc

class BasicProcesssorOpts(object):
    def __init__(self, sources_dir, inp_file):
        self.sources_dir       = sources_dir
        self.inp_file          = inp_file
        self.min_src_docs      = 5
        self.min_sent_per_src  = 4
        self.min_sent_size     = 5
        self.min_real_sent_cnt = 150
        self.mod_type_ratios   = {}
        #допустимый процент изменений для каждого типа сокрытия
        self.diff_perc         = {}

        self.errors_level = ErrSeverity.NORM

class BasicProcessor(object):
    def __init__(self, opts, checkers,
                 metrics,
                 stat_collecter = None):
        self._opts           = opts

        self._checkers       = checkers
        self._metrics        = metrics
        self._stat_collecter = stat_collecter if stat_collecter is not None else StatCollector()


    def _process_chunk(self, chunk, src_docs):

        for checker in self._checkers:
            try:
                checker(chunk, src_docs)
            except Exception as e:
                logging.exception("during proc %d: ", chunk.get_chunk_id())

    def _load_sources_docs(self):
        return source_doc.load_sources_docs(self._opts.sources_dir)



    def _create_chunks(self):
        raise NotImplementedError("Should implement _create_chunks")

    def check(self):

        chunks, errors = self._create_chunks()
        stat = self._stat_collecter(chunks)
        logging.debug("collected stat: %s", stat)
        if stat.chunks_cnt == 0:
            return [Error("Не удалось проанализировать ни один фрагмент",
                          ErrSeverity.HIGH)], stat


        for metric in self._metrics:
            metric(stat, chunks)

        src_docs = self._load_sources_docs()
        for chunk in chunks:
            self._process_chunk(chunk, src_docs)

        for checker in self._checkers:
            errors.extend(e for e in checker.get_errors())

        errors = [e for e in errors if e.sev >= self._opts.errors_level]
        errors.sort(key=lambda e : e.sev, reverse = True)

        return errors, stat
