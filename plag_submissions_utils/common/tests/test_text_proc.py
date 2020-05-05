#!/usr/bin/env python
# coding: utf-8

import unittest

import segtok.segmenter as seg
import segtok.tokenizer as tok

import plag_submissions_utils.common.text_proc as text_proc


class SegTestCase(unittest.TestCase):
    def test_sent_with_trailing_spc(self):
        sent="When most people think of piracy, images of Captain Hook from the story Peter Pan and Captain Blackbeard from the movie Pirates of the Caribbean come to mind. "

        sents = text_proc.seg_text_as_list(sent)
        self.assertEqual(1, len(sents))

    def test_basic(self):
        text = "простое предложение. «второе« 1990 предложение, (и т.д.). 3-е предл."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(3, len(sents))
        self.assertEqual("простое предложение.", sents[0])
        self.assertEqual("«второе« 1990 предложение, (и т.д.).", sents[1])


    def test_year(self):
        text = "В 1982 г. перестало."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))

        text = "В 1982г. перестало."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))
        self.assertEqual("В 1982 г. перестало.", sents[0])

    def test_joint(self):
        text = "заповеди Пифагора.Нравственные устои."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(2, len(sents))
        self.assertEqual("заповеди Пифагора.", sents[0])


class MorphTestCase(unittest.TestCase):
    def test_morph(self):
        text = "Пришедшие люди, ушли ни с чем!"
        tokens = text_proc.tok_sent(text, normalize = True)
        # print tokens
        self.assertEqual(6, len(tokens))
        self.assertEqual('пришедший', tokens[0])
        self.assertEqual('человек', tokens[1])
        self.assertEqual('уйти', tokens[2])


    def test_skip_stop(self):
        text = "Пришедшие люди, ушли ни с чем!"
        tokens = text_proc.tok_sent(text, skip_stop_words = True)
        self.assertEqual(3, len(tokens))
        self.assertEqual('пришедший', tokens[0])
        self.assertEqual('человек', tokens[1])
        self.assertEqual('уйти', tokens[2])
