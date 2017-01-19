#!/usr/bin/env python
# coding: utf-8


import unittest

from plag_submissions_utils.common.chunks import Chunk

class PartialRecordTestCase(unittest.TestCase):
    def test_missing_orig_sent(self):
        ch = Chunk([], "text", "ADD", "filename", "1")
        avg_orig = ch.get_avg_original_words_cnt()
        self.assertEqual(0.0, avg_orig)

    # def test_missing_orig_doc(self):
    #     self.assertRaises(RuntimeError, Chunk, "orig text", "text", "ADD", "", "1")
