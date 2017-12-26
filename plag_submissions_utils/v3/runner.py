#!/usr/bin/env python
# coding: utf-8

import tempfile
import shutil

from plag_submissions_utils.common.extract_utils import extract_submission
import plag_submissions_utils.common.checkers as chks
import plag_submissions_utils.common.metrics as mtrks
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.chunks import TranslatorType

from .processor import ProcessorOpts
from .processor import Processor

def run(archive_path):

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = ProcessorOpts(*extract_submission(archive_path,
                                                 temp_dir))
        checkers = [
            chks.OriginalityChecker(opts),
            chks.OrigSentChecker(opts),
            chks.SourceDocsChecker(opts),
            # chks.PRChecker(opts),
            # chks.AddChecker(opts),
            # chks.DelChecker(opts),
            # chks.CPYChecker(opts),
            # chks.CctChecker(opts),
            # chks.SspChecker(opts),
            # chks.SHFChecker(opts),
            # chks.SYNChecker(opts),
            # chks.LexicalSimChecker(opts),
            chks.ORIGModTypeChecker(),
            chks.SentCorrectnessChecker(),
            chks.SpellChecker(),
            chks.TranslationChecker(opts),
            chks.ManualTranslationChecker(opts)
        ]

        metrics = [mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                   mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size),
                   mtrks.SrcSentsCountMetric(opts.min_src_sents_cnt),
                   mtrks.ModTranslationMetric(opts.max_unmod_translation)
                   ]

        for mod_type in ModType.get_all_mod_types_v2():
            metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                    opts.mod_type_ratios[mod_type]))

        for translation_type in TranslatorType.get_all_translation_types():
            metrics.append(mtrks.AutoTranslationMetric(translation_type,
                                                    opts.translation_type_ratios[translation_type]))

        errors, stat = Processor(opts, checkers, metrics).check()
        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
