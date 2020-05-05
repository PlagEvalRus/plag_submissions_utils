#!/usr/bin/env python
# coding: utf-8


import unittest
import regex

from plag_submissions_utils.common.chunks import Chunk

class PartialRecordTestCase(unittest.TestCase):
    def test_missing_orig_sent(self):
        ch = Chunk([], "text", "ADD", "filename", "1")
        avg_orig = ch.get_avg_original_words_cnt()
        self.assertEqual(0.0, avg_orig)

class ChunksEncodingTestCase(unittest.TestCase):
    def test_regex_matching(self):
        ch = Chunk([], "Онx. yно. оzо", "ADD", "filename", "1")
        r = regex.compile(r'([А-я]*([A-z])[А-я]+|[А-я]+([A-z])[А-я]*)')
        matches = r.findall(ch.get_mod_sents()[0])
        self.assertEqual(3, len(matches))
        self.assertEqual('x', matches[0][2])
        self.assertEqual('y', matches[1][1])
        self.assertEqual('z', matches[2][1])
