#!/usr/bin/env python
# coding: utf-8

import tempfile
import shutil

from plag_submissions_utils.common.extract_utils import extract_submission
import plag_submissions_utils.common.checkers as chks
import plag_submissions_utils.common.metrics as mtrks
from plag_submissions_utils.common.chunks import ModType

from .processor import ProcessorOpts
from .processor import Processor

def run(archive_path):

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = ProcessorOpts(*extract_submission(archive_path,
                                                 temp_dir))
        checkers = [chks.OrigSentChecker(opts),
                    chks.SourceDocsChecker(opts),
                    chks.PRChecker(opts, fluctuation_delta = 5),
                    chks.AddChecker(opts, fluctuation_delta = 5),
                    chks.DelChecker(opts, fluctuation_delta = 5),
                    chks.CPYChecker(opts, fluctuation_delta = 5),
                    chks.CctChecker(opts, fluctuation_delta = 5),
                    chks.SspChecker(opts, fluctuation_delta = 5),
                    chks.ORIGModTypeChecker(),
                    chks.SentCorrectnessChecker(),
                    chks.SpellChecker()]

        metrics = [mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                   mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]

        for mod_type in ModType.get_all_mod_types_v1():
            metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                    opts.mod_type_ratios[mod_type],
                                                    fluctuation_delta=5))
        errors, stat = Processor(opts, checkers, metrics).check()

        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
