#!/usr/bin/env python
# coding: utf-8

import distance

from . import sents
from .source_doc import get_src_filename

class ModType(object):
    UNK  = 0
    CPY  = 1
    LPR  = 2
    HPR  = 3
    ORIG = 4
    DEL  = 5
    ADD  = 6
    CCT  = 7
    SSP  = 8
    #from v2
    SHF  = 9
    SEP  = 10
    SYN  = 11

    @classmethod
    def get_all_mods_type(cls):
        return range(0,9)

def mod_type_to_str(mod_type):
    mod_type_dict = {
        0 : "UNK",
        1 : "CPY",
        2 : "LPR",
        3 : "HPR",
        4 : "ORIG",
        5 : "DEL",
        6 : "ADD",
        7 : "CCT",
        8 : "SSP",
        9 : "SHF",
        10 : "SEP",
        11 : "SYN"
    }
    return mod_type_dict.get(mod_type, "unk")

def _create_mod_type(mod_str):
    mls = mod_str.strip().lower()
    if not mls:
        return ModType.ORIG
    elif mls == "cpy":
        return ModType.CPY
    elif mls == "lpr":
        return ModType.LPR
    elif mls == "hpr":
        return ModType.HPR
    elif mls == "del":
        return ModType.DEL
    elif mls == "add":
        return ModType.ADD
    elif mls == "ssp":
        return ModType.SSP
    elif mls == "cct":
        return ModType.CCT
    elif mls == "shf":
        return ModType.SHF
    elif mls == "sep":
        return ModType.SEP
    elif mls == "syn":
        return ModType.SYN
    else:
        return ModType.UNK


class Chunk(object):
    def __init__(self, orig_text, mod_text,
                 mod_type_str, orig_doc, chunk_num):
        self._chunk_num           = chunk_num
        self._original_sents      = sents.SentsHolder(orig_text)
        self._modified_sents      = sents.SentsHolder(mod_text)
        self._mod_type            = _create_mod_type(mod_type_str)
        self._orig_doc            = orig_doc


    def get_chunk_id(self):
        return self._chunk_num

    def get_mod_type(self):
        return self._mod_type

    def get_orig_doc(self):
        return self._orig_doc

    def get_orig_doc_filename(self):
        return get_src_filename(self._orig_doc)

    def get_avg_original_words_cnt(self):
        return self._original_sents.get_avg_words_cnt()

    def get_avg_modified_words_cnt(self):
        return self._modified_sents.get_avg_words_cnt()

    def measure_dist(self):
        return distance.nlevenshtein(self._original_sents.get_all_tokens(),
                                     self._modified_sents.get_all_tokens())

    def get_orig_sents(self):
        return self._original_sents.get_sents()

    def get_modified_sents(self):
        return self._modified_sents.get_sents()

    def get_orig_tokens(self):
        return self._original_sents.get_all_tokens()

    def get_orig_tokens_list(self):
        return self._original_sents.get_tokens_list()

    def get_mod_tokens(self):
        return self._modified_sents.get_all_tokens()

    def get_orig_text(self):
        return self._original_sents.get_text()

    def get_mod_text(self):
        return self._modified_sents.get_text()

    def __str__(self):
        chunk_str = "%d (%s): %s, %s" %(
            self._chunk_num,
            mod_type_to_str(self._mod_type),
            u" ".join(self._modified_sents.get_sents()).encode("utf8"),
            u"|".join(self._modified_sents.get_all_tokens()).encode("utf8"))
        return chunk_str
