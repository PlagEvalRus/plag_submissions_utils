#!/usr/bin/env python
# coding: utf-8

import unittest

import segtok.segmenter as seg
import segtok.tokenizer as tok

import plag_submissions_checker.common.text_proc as text_proc

class SegtokTestCase(object):
    def test(self):
        #TODO
        test_sent = u"простое предложение."
        without_mark_sent = u"простое предложение без знака"
        three_sents = u"простое предложение. «второе« 1990 предложение, (и т.д.). 2. почем"


        sents = seg.split_single(test_sent)
        print "|".join(s.encode("utf8") for s in sents)
        sents = seg.split_single(without_mark_sent)
        print "|".join(s.encode("utf8") for s in sents)
        sents = [s for s in seg.split_single(three_sents)]
        print u"|".join(sents)

        tokens = tok.space_tokenizer(sents[1])
        print "<>".join(s for s in tokens)

        tokens = tok.symbol_tokenizer(sents[1])
        print "<>".join(s for s in tokens if not text_proc.ispunct(s))

        # tokens = tok.symbol_tokenizer(sents[1])
        # print "<>".join(s for s in tokens)


class SegTestCase(unittest.TestCase):
    def test_sent_with_trailing_spc(self):
        sent=u"When most people think of piracy, images of Captain Hook from the story Peter Pan and Captain Blackbeard from the movie Pirates of the Caribbean come to mind. "

        sents = text_proc.seg_text_as_list(sent)
        self.assertEqual(1, len(sents))
