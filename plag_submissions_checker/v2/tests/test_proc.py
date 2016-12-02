#!/usr/bin/env python
# coding: utf-8

import unittest

import plag_submissions_checker.v2.runner as runner

class ProcessorTestCase(unittest.TestCase):

    def _process_file(self, archive_path):
        return runner.run(archive_path)

    def test_file(self):
        metrics, errors, stat = self._process_file("data/test_data_v2/test.zip")
        self.assertEqual(0, len(errors), "errors:\n%s" % '\n'.join(str(e) for e in errors))
        self.assertEqual(100, stat.chunks_cnt)
