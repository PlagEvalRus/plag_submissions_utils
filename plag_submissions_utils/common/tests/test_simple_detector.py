#!/usr/bin/env python
# coding: utf-8

import unittest

from plag_submissions_utils.common.simple_detector import SimpleDetector
from plag_submissions_utils.common.simple_detector import SimpleDetectorOpts
from plag_submissions_utils.common.simple_detector import calc_originality_by_detections

class SimpleDetectorTestCase(unittest.TestCase):
    def setUp(self):
        opts = SimpleDetectorOpts(5)
        self.detector = SimpleDetector(opts)

    def test_literal_case(self):
        susp_text = "Тест text!!!!"
        src_text = susp_text

        detections = self.detector(susp_text, src_text)

        self.assertEqual(1, len(detections))
        susp_beg, susp_end = detections[0][1]
        src_beg, src_end = detections[0][0]


        self.assertEqual(13, susp_end)
        self.assertEqual(13, src_end)

        originality = calc_originality_by_detections(detections, susp_text)
        self.assertAlmostEqual(0.0, originality, 3)


    def test_changed_case(self):
        susp_text = "Тест text!!!!Text Other bla-bla!"
        src_text = "Good text!!Test Another code!"

        detections = self.detector(susp_text, src_text)

        self.assertEqual(2, len(detections))
        susp_beg, susp_end = detections[0][1]
        src_beg, src_end = detections[0][0]
        self.assertEqual(5, susp_beg)
        self.assertEqual(15, susp_end)
        self.assertEqual(5, src_beg)
        self.assertEqual(13, src_end)

        #matched only othe; 'r' is skipped. Why?
        susp_beg2, susp_end2 = detections[1][1]
        src_beg2, src_end2 = detections[1][0]
        self.assertEqual(18, susp_beg2)
        self.assertEqual(22, susp_end2)
        self.assertEqual(18, src_beg2)
        self.assertEqual(22, src_end2)

        originality = calc_originality_by_detections(detections, susp_text)
        self.assertAlmostEqual(18.0/32, originality, 3)
