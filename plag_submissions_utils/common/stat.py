#!/usr/bin/env python
# coding: utf-8

import itertools
from collections import defaultdict


from .chunks import ModType
from .chunks import mod_types_to_str

class SubmissionStat(object):
    """Documentation for SubmissionStat

    """
    def __init__(self, chunks_cnt,
                 orig_sent_lengths = None,
                 mod_sent_lengths = None,
                 mod_type_freqs = None,
                 docs_freqs = None,
                 src_sents_cnt = 0):
        super(SubmissionStat, self).__init__()
        self.chunks_cnt        = chunks_cnt
        self.orig_sent_lengths = orig_sent_lengths if orig_sent_lengths is not None else []
        self.mod_sent_lengths  = mod_sent_lengths if mod_sent_lengths is not None else []
        self.mod_type_freqs    = mod_type_freqs if mod_type_freqs is not None else \
                                 defaultdict(lambda : 0)
        self.mod_type_co_occur = defaultdict(lambda : 0)

        self.docs_freqs        = docs_freqs if docs_freqs is not None else defaultdict(lambda : 0)
        self.src_sents_cnt     = src_sents_cnt

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
        self._stat = SubmissionStat(0)

    def _update_co_occurs(self, mod_types, stat):
        for comb_size in [2,3,4,5]:
            for comb in itertools.combinations(mod_types, comb_size):
                t = tuple(sorted(comb))
                stat.mod_type_co_occur[t] += 1

    def get_stat(self):
        return self._stat

    def mod_types_stat(self):
        items = self._stat.mod_type_co_occur.items()
        items.sort(key = lambda t : t[1], reverse=True)
        return items, self._stat.mod_type_freqs

    def __call__(self, chunks):
        self._stat.chunks_cnt += len(chunks)
        for chunk in chunks:
            if chunk.get_mod_type() != ModType.ORIG:
                self._stat.orig_sent_lengths.append((chunk.get_chunk_id(),
                                                     chunk.get_avg_original_words_cnt()))
                self._stat.docs_freqs[chunk.get_orig_doc_filename()] += 1
                self._stat.src_sents_cnt += len(chunk.get_orig_sents())


            self._stat.mod_sent_lengths.append((chunk.get_chunk_id(),
                                                chunk.get_avg_modified_words_cnt()))

            for mod_type in chunk.get_all_mod_types():
                self._stat.mod_type_freqs[mod_type] += 1
            self._update_co_occurs(chunk.get_all_mod_types(), self._stat)

        return self._stat

def collect_stat(chunks):
    return StatCollector()(chunks)

def print_mod_types_stat(stat_holder, out):
    co_occur, freqs = stat_holder.mod_types_stat()
    out.write("Types frequencies\n")
    for freq in freqs:
        out.write("%s: %d\n" % (mod_types_to_str([freq]), freqs[freq]))

    out.write("Co-occurrences:\n")
    for types, freq in co_occur:
        out.write("%s: %d\n" % (mod_types_to_str(types), freq))