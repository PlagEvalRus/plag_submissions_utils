#!/usr/bin/env python
# coding: utf-8

import unittest

import plag_submissions_utils.v2.runner as runner
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common_runner import _metrics_violations_cnt
from plag_submissions_utils.common.metrics import ViolationLevel

class ProcessorTestCase(unittest.TestCase):

    def _process_file(self, archive_path):
        return runner.run(archive_path)

    def test_file(self):
        metrics, errors, stat = self._process_file("data/test_data_v2/test.zip")
        # print stat
        self.assertEqual(4, len(errors), "errors:\n%s" % '\n'.join(str(e) for e in errors))
        self.assertEqual(100, stat.chunks_cnt)

        self.assertEqual(10, stat.mod_type_freqs[ModType.UNK])

        self.assertEqual(5, stat.docs_freqs["1"])
        self.assertEqual(14, stat.docs_freqs["8"])
        self.assertEqual(14, stat.docs_freqs["2"])

        self.assertEqual(1, _metrics_violations_cnt(
            metrics, ViolationLevel.HIGH))
