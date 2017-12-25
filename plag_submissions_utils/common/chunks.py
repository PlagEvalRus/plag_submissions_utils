#!/usr/bin/env python
# coding: utf-8

import logging
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
    def get_all_mod_types_v1(cls):
        return range(0,9)

    @classmethod
    def get_all_mod_types_v2(cls):
        return range(0,8) + range(9,12)

def mod_types_to_str(mod_types):
    return ",".join(mod_type_to_str(m) for m in mod_types)

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

def _create_mod_types(mods_str):
    return [_create_mod_type(m) for m in mods_str.split(',')]

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


class TranslatorType(object):
    UNK      = 0
    GOOGLE   = 1
    YANDEX   = 2
    ORIGINAL = 3
    MANUAL   = 4

    @classmethod
    def get_all_translation_types(cls):
        return range(0,5)

def translation_types_to_str(translation_types):
    return ",".join(translation_type_to_str(m) for m in translation_types)

def translation_type_to_str(translation_type):
    translation_type_dict = {
        0 : "UNK",
        1 : "GOOGLE",
        2 : "YANDEX",
        3 : "ORIGINAL",
        4 : "MANUAL"
    }
    return translation_type_dict.get(translation_type, "unk")

def _create_translation_types(translations_str, orig_str):
    return [_create_translation_type(m, orig_str) for m in translations_str.split(',')]

def _create_translation_type(translation_str, orig_str):
    tls = translation_str.strip().lower()
    if tls == "yandex":
        return TranslatorType.YANDEX
    elif tls == "google":
        return TranslatorType.GOOGLE
    elif tls == "-" and len(orig_str) == 0:
        return TranslatorType.ORIGINAL
    elif tls == "-":
        return TranslatorType.MANUAL
    else:
        return ModType.UNK


class ChunkOpts(object):
    def __init__(self, normalize = False,
                 skip_stop_words = False):
        self.normalize = normalize
        self.skip_stop_words = skip_stop_words


class Chunk(object):
    def __init__(self, orig_text, mod_text,
                 mod_type_str, orig_doc, chunk_num,
                 opts = ChunkOpts(), translated_text=None, translator_type_str=None):
        self._chunk_num           = chunk_num
        self._original_sents      = sents.SentsHolder(orig_text, opts)
        if translated_text:
            self._translated_sents    = sents.SentsHolder(translated_text, opts)
        self._modified_sents      = sents.SentsHolder(mod_text, opts)

        logging.debug("input mode type string: %s", mod_type_str)
        self._mod_types           = _create_mod_types(mod_type_str)
        if translator_type_str:
            self._translator_types    = _create_translation_types(translator_type_str, orig_text)
        self._orig_doc            = orig_doc


    def get_chunk_id(self):
        return self._chunk_num

    def get_mod_type(self):
        """If chunk has only one modification type, this one will be returned.
        If there are many types (like in v2), UNK is returned.
        """
        if len(self._mod_types) == 1:
            return self._mod_types[0]
        else:
            return ModType.UNK

    def get_all_mod_types(self):
        return self._mod_types

    def has_mod_type(self, mod_type):
        return mod_type in self._mod_types

    def get_translator_type(self):
        if len(self._translator_types) == 1:
            return self._translator_types[0]
        else:
            return TranslatorType.UNK

    def get_translator_type_str(self):
        if self._translator_types[0] == 1:
            return 'google'
        elif self._translator_types[0] == 2:
            return 'yandex'
        else:
            return TranslatorType.UNK

    def get_all_translator_types(self):
        return self._translator_types

    def has_translator_type(self, translator_type):
        return translator_type in self._translator_types

    def get_orig_doc(self):
        return self._orig_doc

    def get_orig_doc_filename(self):
        return get_src_filename(self._orig_doc)

    def get_avg_original_words_cnt(self):
        return self._original_sents.get_avg_words_cnt()

    def get_avg_mod_words_cnt(self):
        return self._modified_sents.get_avg_words_cnt()

    def measure_dist(self):
        return distance.nlevenshtein(self.get_orig_tokens(),
                                     self.get_mod_tokens())

    def lexical_dist(self):
        return distance.jaccard(self.get_orig_tokens(),
                                self.get_mod_tokens())

    def get_mod_sent_holder(self):
        return self._modified_sents

    def get_orig_sent_holder(self):
        return self._original_sents

    def get_translated_sent_holder(self):
        return self._translated_sents

    def get_orig_sents(self):
        return self._original_sents.get_sents()

    def get_translated_sents(self):
        return self._translated_sents.get_sents()

    def get_mod_sents(self):
        return self._modified_sents.get_sents()

    def get_orig_tokens(self):
        return self._original_sents.get_all_tokens()

    def get_orig_tokens_list(self):
        return self._original_sents.get_tokens_list()

    def get_mod_tokens(self):
        """Tokens are lowercased.
        """
        return self._modified_sents.get_all_tokens()

    def get_orig_text(self):
        return self._original_sents.get_text()

    def get_mod_text(self):
        return self._modified_sents.get_text()

    def __str__(self):
        chunk_str = "%d (%s): %s, %s" %(
            self._chunk_num,
            mod_types_to_str(self._mod_types),
            u" ".join(self.get_mod_sents()).encode("utf8"),
            u"|".join(self.get_mod_tokens()).encode("utf8"))
        return chunk_str
