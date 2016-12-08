#!/usr/bin/env python
# coding: utf-8

import logging
import unittest

import plag_submissions_checker.common.checkers  as chks
from plag_submissions_checker.common.chunks import Chunk
from plag_submissions_checker.common.errors import ErrSeverity

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
