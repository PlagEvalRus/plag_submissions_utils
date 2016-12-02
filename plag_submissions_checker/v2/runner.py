#!/usr/bin/env python
# coding: utf-8


import tempfile
import shutil

from plag_submissions_checker.common.extract_utils import extract_submission
# import plag_submissions_checker.common.checkers as chks
# import plag_submissions_checker.common.metrics as mtrks
# from plag_submissions_checker.common.chunks import ModType

from .processor import ProcessorOpts
from .processor import Processor

def run(archive_path):

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = ProcessorOpts(*extract_submission(archive_path,
                                                 temp_dir))
        checkers = []
        metrics = []
        errors, stat = Processor(opts, checkers, metrics).check()
        return metrics, errors, stat

    finally:
        shutil.rmtree(temp_dir)
