#!/usr/bin/env python
# coding: utf-8

from collections import defaultdict


from .chunks import ModType

class SubmissionStat(object):
    """Documentation for SubmissionStat

    """
    def __init__(self, chunks_cnt,
                 orig_sent_lengths = None,
                 mod_sent_lengths = None,
                 mod_type_freqs = None,
                 docs_freqs = None):
        super(SubmissionStat, self).__init__()
        self.chunks_cnt        = chunks_cnt
        self.orig_sent_lengths = orig_sent_lengths if orig_sent_lengths is not None else []
        self.mod_sent_lengths  = mod_sent_lengths if mod_sent_lengths is not None else []
        self.mod_type_freqs    = mod_type_freqs if mod_type_freqs is not None else defaultdict(lambda : 0)
        self.docs_freqs        = docs_freqs if docs_freqs is not None else defaultdict(lambda : 0)

    def _defdict_to_str(self, defdict, val_trans = lambda v: v, key_trans = lambda k : k):
        return "\n".join("%s : %s" % (key_trans(k), val_trans(v)) for k, v in defdict.iteritems())

    def __str__(self):
        len_parts = []
        for num in range(len(self.orig_sent_lengths)):
            len_parts.append("%d: %f, %f" %(self.orig_sent_lengths[num][0],
                                            self.mod_sent_lengths[num][1],
                                            self.orig_sent_lengths[num][1]))


        return """Total chunks cnt: %d
Sent lengths: %s
Mod type frequencies: %s
Docs frequencies: %s""" %(self.chunks_cnt,
                          "\n".join(len_parts),
                          self._defdict_to_str(self.mod_type_freqs),
                          self._defdict_to_str(self.docs_freqs, key_trans = lambda k: k.encode("utf8")))



class StatCollector(object):
    def __init__(self):
        pass

    def __call__(self, chunks):
        stat = SubmissionStat(len(chunks))
        for chunk in chunks:
            stat.orig_sent_lengths.append((chunk.get_chunk_id(),
                                           chunk.get_avg_original_words_cnt()))

            stat.mod_sent_lengths.append((chunk.get_chunk_id(),
                                          chunk.get_avg_modified_words_cnt()))

            stat.mod_type_freqs[chunk.get_mod_type()] += 1
            if chunk.get_mod_type() != ModType.ORIG:
                stat.docs_freqs[chunk.get_orig_doc()] += 1

        return stat
