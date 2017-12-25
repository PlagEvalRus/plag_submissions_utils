#!/usr/bin/env python
# coding: utf-8


from .common.metrics import ViolationLevel
from .common.errors import ErrSeverity
from .common.version import determine_version_by_id
from .common.chunks import ChunkOpts

from .v1 import runner as v1run
from .v2 import runner as v2run
from .v3 import runner as v3run
from .v1 import processor as v1_proc
from .v2 import processor as v2_proc
from .v3 import processor as v3_proc

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

def fatal_errors_cnt(metrics, errors, stat):
    return _metrics_violations_cnt(metrics, ViolationLevel.FATAL)


def run(archive_path, version):
    if version   == "1":
        return v1run.run(archive_path)
    elif version == "2":
        return v2run.run(archive_path)
    elif version == "3":
        return v3run.run(archive_path)
    else:
        raise RuntimeError("Unknown version: %s!" % version)


def create_chunks(susp_id, meta_file_path, version=None,
                  opts = ChunkOpts()):
    if version is None:
        version = determine_version_by_id(susp_id)

    if version   == "1":
        return v1_proc.create_chunks(meta_file_path, opts)
    elif version == "2":
        return v2_proc.create_chunks(meta_file_path, opts)
    elif version == "3":
        return v3_proc.create_chunks(meta_file_path, opts)
    else:
        raise RuntimeError("Unknown version: %s" % version)
