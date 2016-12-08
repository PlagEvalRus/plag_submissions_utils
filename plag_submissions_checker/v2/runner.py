#!/usr/bin/env python
# coding: utf-8


import tempfile
import shutil

from plag_submissions_checker.common.extract_utils import extract_submission
import plag_submissions_checker.common.checkers as chks
import plag_submissions_checker.common.metrics as mtrks
from plag_submissions_checker.common.chunks import ModType

from .processor import ProcessorOpts
from .processor import Processor

def run(archive_path):

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = ProcessorOpts(*extract_submission(archive_path,
                                                 temp_dir))
        checkers = [
            chks.OrigSentChecker(opts),
            chks.SourceDocsChecker(opts),
            chks.PRChecker(opts),
            chks.AddChecker(opts),
            chks.DelChecker(opts),
            chks.CPYChecker(opts),
            chks.CctChecker(opts),
            chks.SspChecker(opts),
            chks.SHFChecker(opts),
            chks.SYNChecker(opts),
            chks.LexicalSimChecker(opts),
            chks.ORIGModTypeChecker()
        ]

        metrics = [mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                   mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]

        for mod_type in ModType.get_all_mod_types_v2():
            metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                    opts.mod_type_ratios[mod_type]))
        errors, stat = Processor(opts, checkers, metrics).check()
        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
