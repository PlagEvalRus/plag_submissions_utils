#!/usr/bin/env python
# coding: utf-8

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
    def __init__(self, text, opts, segment = False):
        super(SentsHolder, self).__init__()
        self._opts = opts
        if isinstance(text, (list, )):
            #It is possible in essays of version 2.
            #Original text is already segmented by writer!
            self._sents = [s.strip() for s in text]
        else:
            if segment:
                self._sents = text_proc.seg_text_as_list(text)
            else:
                self._sents = [text.strip()]

        self._sents = [s for s in self._sents if len(s) > 1]


        self._sent_tokens = [text_proc.tok_sent(s, normalize = opts.normalize,
                                                skip_stop_words = opts.skip_stop_words)
                             for s in self._sents]
        self._sent_infos = [SentInfo(len(t)) for t in self._sent_tokens]

    def get_avg_words_cnt(self):
        if not self._sent_infos:
            return 0.0
        words_cnt = sum(si.word_cnt for si in self._sent_infos)
        return float(words_cnt)/ len(self._sent_infos)

    def get_sent_info(self, sent_num):
        return self._sent_infos[sent_num]

    def add_sent(self, sent, tokenize = True):
        self._sents.append(sent)
        if tokenize:
            tokens = text_proc.tok_sent(sent,
                                        normalize = self._opts.normalize,
                                        skip_stop_words = self._opts.skip_stop_words)
            self._sent_tokens.append(tokens)
            self._sent_infos.append(SentInfo(len(tokens)))


    def get_sents(self):
        return self._sents

    def get_text(self):
        return ' '.join(self._sents)

    def get_all_tokens(self):
        all_tokens = []
        for t in self._sent_tokens:
            all_tokens.extend(t)
        return all_tokens

    def get_tokens_list(self):
        return self._sent_tokens
