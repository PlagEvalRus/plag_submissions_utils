#!/usr/bin/env python
# coding: utf-8

import tempfile
import shutil

from plag_submissions_utils.common.extract_utils import extract_submission
import plag_submissions_utils.common.checkers as chks
import plag_submissions_utils.common.translation_checkers as trans_chks
import plag_submissions_utils.common.metrics as mtrks
import plag_submissions_utils.common.translation_metrics as trans_mtrks
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.translated_chunks import TranslatorType

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
            chks.PRChecker(opts),
            # chks.AddChecker(opts),
            # chks.DelChecker(opts),
            # chks.CPYChecker(opts),
            chks.CctChecker(opts),
            # chks.SspChecker(opts),
            chks.SHFChecker(opts),
            # chks.SYNChecker(opts),
            chks.LexicalSimChecker(opts),
            trans_chks.ORIGModTypeChecker(),
            chks.SentCorrectnessChecker(),
            chks.SpellChecker(),
            trans_chks.TranslationChecker(opts),
            trans_chks.ManualTranslationChecker(opts),
            chks.CyrillicAlphabetChecker(opts)
        ]

        metrics = [
            mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
            mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size),
            trans_mtrks.ModTranslationMetric(opts.max_unmod_translation),
            mtrks.MeanSentLenMetric(opts.min_mean_sent_len)
        ]

        for mod_type in ModType.get_all_mod_types_v3():
            metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                    opts.mod_type_ratios[mod_type]))

        for translation_type in TranslatorType.get_all_translation_types():
            metrics.append(
                trans_mtrks.AutoTranslationMetric(translation_type,
                                                  opts.translation_type_ratios[translation_type]))

        errors, stat = Processor(opts, checkers, metrics).check()
        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
