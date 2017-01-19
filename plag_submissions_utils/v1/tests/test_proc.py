#!/usr/bin/env python
# coding: utf-8

import unittest

import plag_submissions_utils.v1.runner as runner

class ProcessorTestCase(unittest.TestCase):

    def _process_file(self, archive_path):
        return runner.run(archive_path)

    def test_file(self):
        metrics, errors, stat = self._process_file("data/test_data/test.zip")
        self.assertEqual(152, stat.chunks_cnt)
