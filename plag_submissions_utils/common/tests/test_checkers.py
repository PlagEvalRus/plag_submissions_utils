#!/usr/bin/env python
# coding: utf-8

import logging
import unittest

import plag_submissions_utils.common.checkers  as chks
from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.errors import ErrSeverity

from plag_submissions_utils.v1.processor import ProcessorOpts
from plag_submissions_utils.v1.processor import Processor


class Opts(object):
    """Documentation for Opts

    """
    def __init__(self, min_dist=30):
        super(Opts, self).__init__()
        self.min_lexical_dist = min_dist


class LexicalSimCheckerTestCase(unittest.TestCase):

    def setUp(self):
        self.checker = chks.LexicalSimChecker(Opts())

    def simple_test(self):
        chunk = Chunk("Text about animals.",
                      "Text - about = animals.",
                      "LPR,ADD", "rvan'", 1)
        self.checker(chunk, None)

        errors = self.checker.get_errors()
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.HIGH, errors[0].sev)

    def simple_test2(self):
        chunk = Chunk("Text about animals in the wild.",
                      "Text - about = animals in a wild.",
                      "LPR", "rvan'", 1)
        logging.debug(chunk)
        self.checker(chunk, None)

        errors = self.checker.get_errors()
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.NORM, errors[0].sev)


class ORIGModTypeCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.checkers = [chks.ORIGModTypeChecker()]

    def test_submission(self):
        opts = ProcessorOpts("data/test_data/test_orig_mod_type/sources",
                             "data/test_data/test_orig_mod_type/sources_list.xlsx")
        errors, _ = Processor(opts, self.checkers, []).check()

        self.assertEqual(2, len(errors))
