#!/usr/bin/env python
# coding: utf-8

import tempfile
import shutil

from . import submission_checker_utils as scu

def _metrics_violations_cnt(metrics, level):
    return len([1 for m in metrics if m.get_violation_level() == level] )

def _errors_cnt(errors, level):
    return len([1 for e in errors if e.sev == level])


def serious_errors_cnt(metrics, errors, stat):
    return _metrics_violations_cnt(metrics, scu.ViolationLevel.HIGH) + \
        _errors_cnt(errors, scu.ErrSeverity.HIGH)

def medium_errors_cnt(metrics, errors, stat, count_metrics = True):
    if count_metrics:
        errs = _metrics_violations_cnt(metrics, scu.ViolationLevel.MEDIUM)
    else:
        errs = 0
    return errs + \
        _errors_cnt(errors, scu.ErrSeverity.NORM)


def run(archive_path):

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = scu.PocesssorOpts(*scu.extract_submission(archive_path,
                                                         temp_dir))
        checkers = [scu.OrigSentChecker(opts),
                    scu.SourceDocsChecker(opts),
                    scu.PRChecker(opts),
                    scu.AddChecker(opts),
                    scu.DelChecker(opts),
                    scu.CPYChecker(opts),
                    scu.CctChecker(opts),
                    scu.SspChecker(opts),
                    scu.ORIGModTypeChecker()]
        metrics = [scu.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                   scu.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]
        for mod_type in scu.ModType.get_all_mods_type():
            metrics.append(scu.ModTypeRatioMetric(mod_type,
                                                  opts.mod_type_ratios[mod_type]))
        errors, stat = scu.Processor(opts, checkers, metrics).check()

        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
