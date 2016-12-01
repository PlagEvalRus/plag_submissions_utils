#!/usr/bin/env python
# coding: utf-8


from .common.metrics import ViolationLevel
from .common.errors import ErrSeverity

from .v1 import runner as v1run

def _metrics_violations_cnt(metrics, level):
    return len([1 for m in metrics if m.get_violation_level() == level] )

def _errors_cnt(errors, level):
    return len([1 for e in errors if e.sev == level])


def serious_errors_cnt(metrics, errors, stat):
    return _metrics_violations_cnt(metrics, ViolationLevel.HIGH) + \
        _errors_cnt(errors, ErrSeverity.HIGH)

def medium_errors_cnt(metrics, errors, stat, count_metrics = True):
    if count_metrics:
        errs = _metrics_violations_cnt(metrics, ViolationLevel.MEDIUM)
    else:
        errs = 0
    return errs + \
        _errors_cnt(errors, ErrSeverity.NORM)


def run(archive_path, version):
    if version == "1":
        return v1run.run(archive_path)
    elif version == "2":
        pass
    else:
        raise RuntimeError("Unknown version: %s!" % version)
