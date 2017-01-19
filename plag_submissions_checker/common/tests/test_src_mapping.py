#!/usr/bin/env python
# coding: utf-8

import tempfile

import unittest

from plag_submissions_checker.common.extract_utils import extract_submission
from plag_submissions_checker.common import src_mapping


class SrcMapTestCase(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.mkdtemp()
        self.sources_dir, _ = extract_submission("data/test_data_v2/test.zip",
                                                 temp_dir)
        self.mapping = src_mapping.SrcMap()

    def test_filename_as_id(self):
        src_mapping.add_src_from_dir("1", self.sources_dir, self.mapping,
                                     True)
        src1 = self.mapping.get_src_by_filename("1", "1")
        self.assertEqual(1, src1.get_ext_id())

        src4 = self.mapping.get_src_by_filename("1", "4")
        self.assertEqual(4, src4.get_ext_id())

    def test_generated_id(self):
        src_mapping.add_src_from_dir("1", self.sources_dir, self.mapping)
        src1 = self.mapping.get_src_by_filename("1", "1")
        self.assertEqual(64, src1.get_ext_id())
