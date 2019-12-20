#!/usr/bin/env python
# coding: utf-8

import logging

from .stats import collect_stat
from .errors import ErrSeverity
from .errors import Error
from . import source_doc

class BasicProcesssorOpts(object):
    def __init__(self):
        self.min_src_docs      = 5
        self.min_sent_per_src  = 4
        self.min_sent_size     = 5
        self.min_real_sent_cnt = 150
        self.mod_type_ratios   = {}
        self.translation_type_ratios   = {}
        #допустимый процент изменений для каждого типа сокрытия
        self.diff_perc         = {}

        self.errors_level = ErrSeverity.NORM

class BasicProcessor(object):
    def __init__(self, opts, checkers,
                 metrics):
        self._opts           = opts

        self._checkers       = checkers
        self._metrics        = metrics


    def _process_chunk(self, chunk, src_docs):

        for checker in self._checkers:
            try:
                checker(chunk, src_docs)
            except Exception as e:
                logging.exception("during proc %d: ", chunk.get_chunk_id())

    def _load_sources_docs(self, sources_dir):
        return source_doc.load_sources_docs(sources_dir)



    def _create_chunks(self, inp_file):
        raise NotImplementedError("Should implement _create_chunks")

    def check(self, sources_dir, inp_file):

        chunks, errors = self._create_chunks(inp_file)
        stat = collect_stat(chunks)
        logging.debug("collected stat: %s", stat)
        if stat.chunks_cnt == 0:
            errors.append(Error("Не удалось проанализировать ни один фрагмент",
                                ErrSeverity.HIGH))
            return  errors, stat


        for metric in self._metrics:
            metric(stat, chunks)

        src_docs = self._load_sources_docs(sources_dir)
        for chunk in chunks:
            self._process_chunk(chunk, src_docs)

        for checker in self._checkers:
            errors.extend(e for e in checker.get_errors())

        errors = [e for e in errors if e.sev >= self._opts.errors_level]
        errors.sort(key=lambda e : e.sev, reverse = True)

        return errors, stat
