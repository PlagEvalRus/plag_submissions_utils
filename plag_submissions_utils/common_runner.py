#!/usr/bin/env python
# coding: utf-8

import tempfile
import shutil
import logging
import importlib

from .common.metrics import ViolationLevel
from .common.errors import ErrSeverity
from .common.version import determine_version_by_id
from .common.chunks import ChunkOpts
from .common.extract_utils import extract_submission

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
    temp_dir = tempfile.mkdtemp()
    try:
        mod = _import(version)

        sources_dir, inp_file = extract_submission(archive_path, temp_dir)
        opts = mod.ProcessorOpts()
        checkers = mod.create_checkers(opts, sources_dir)
        metrics = mod.create_metrics(opts, sources_dir)

        proc = mod.Processor(opts, checkers, metrics)
        errors, stat = proc.check(sources_dir, inp_file)

        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)


def _import(version):
    return importlib.import_module('.processor', 'plag_submissions_utils.v' + version)

def _create_chunks(version, meta_filepath, opts = ChunkOpts()):
    mod = _import(version)
    return getattr(mod, 'create_chunks')(meta_filepath, opts)

def _create_xlsx_from_chunks(version, chunks, out_dir):
    mod = _import(version)
    return getattr(mod, 'create_xlsx_from_chunks')(chunks, out_dir + '/sources_list.xlsx')



def create_chunks(susp_id, meta_filepath, version=None,
                  opts = ChunkOpts()):
    if version is None:
        version = determine_version_by_id(susp_id)

    return _create_chunks(version, meta_filepath, opts)


def fix(archive_path, out_filename, version):
    temp_dir, new_dir = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        sources_dir, meta_filepath = extract_submission(archive_path, temp_dir)

        chunks, errors = _create_chunks(version, meta_filepath)
        for err in errors:
            logging.error(err)

        #TODO Fix chunks

        _create_xlsx_from_chunks(version, chunks, new_dir)
        shutil.move(sources_dir, new_dir)
        shutil.make_archive(out_filename, 'zip', new_dir)
    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(new_dir)
