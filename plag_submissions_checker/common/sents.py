#!/usr/bin/env python
# coding: utf-8

import segtok.segmenter as seg
import segtok.tokenizer as tok

from . import text_proc

class SentInfo(object):
    """Documentation for SentInfo

    """
    def __init__(self, word_cnt):
        super(SentInfo, self).__init__()
        self.word_cnt = word_cnt


def create_sent_info(sent):
    tokens = text_proc.tok_sent(sent)
    return SentInfo(len(tokens))

class SentsHolder(object):
    """Documentation for SentsHolder

    """
    def __init__(self, text):
        super(SentsHolder, self).__init__()
        self._text       = text
        self._sents      = text_proc.seg_text_as_list(text)
        self._sent_tokens = [text_proc.tok_sent(s) for s in self._sents]
        self._sent_infos = [SentInfo(len(t)) for t in self._sent_tokens]

    def get_avg_words_cnt(self):
        words_cnt = sum(si.word_cnt for si in self._sent_infos)
        return float(words_cnt)/ len(self._sent_infos)

    def get_sents(self):
        return self._sents

    def get_text(self):
        return self._text

    def get_all_tokens(self):
        all_tokens = []
        for t in self._sent_tokens:
            all_tokens.extend(t)
        return all_tokens

    def get_tokens_list(self):
        return self._sent_tokens
