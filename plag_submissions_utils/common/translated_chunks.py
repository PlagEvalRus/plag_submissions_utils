#!/usr/bin/env python
# coding: utf-8

import distance

from . import sents
from . import chunks

class TranslatorType(object):
    UNK      = 0
    GOOGLE   = 1
    YANDEX   = 2
    ORIGINAL = 3
    MANUAL   = 4

    @classmethod
    def get_all_translation_types(cls):
        return list(range(0,5))

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
    if tls == "google":
        return TranslatorType.GOOGLE
    if tls == "original" or (tls == '-' and not orig_str):
        return TranslatorType.ORIGINAL
    if tls == "manual" or tls == '-':
        return TranslatorType.MANUAL
    return chunks.ModType.UNK


class TranslatedChunk(chunks.Chunk):
    def __init__(self, orig_text, mod_text,
                 mod_type_str, orig_doc, chunk_num,
                 translator_type_str=None, translated_text=None, opts = chunks.ChunkOpts()):

        super().__init__(orig_text, mod_text, mod_type_str,
                         orig_doc, chunk_num, opts)

        self._translated_sents    = sents.SentsHolder(translated_text, opts)

        self._translator_types    = _create_translation_types(translator_type_str, orig_text)


    def get_translator_type(self):
        if len(self._translator_types) == 1:
            return self._translator_types[0]
        return TranslatorType.UNK

    def get_translator_type_str(self):
        return translation_types_to_str(self._translator_types)

    def get_all_translator_types(self):
        return self._translator_types

    def has_translator_type(self, translator_type):
        return translator_type in self._translator_types

    def measure_dist(self):
        return distance.nlevenshtein(self.get_translated_tokens(),
                                     self.get_mod_tokens())

    def lexical_dist(self):
        return distance.nlevenshtein(self.get_translated_tokens(),
                                     self.get_mod_tokens())

    def get_translated_sent_holder(self):
        return self._translated_sents

    def get_translated_sents(self):
        return self._translated_sents.get_sents()

    # def has_translated_sents(self):
    #     try:
    #         return self._translated_sents
    #     except AttributeError:
    #         return False

    def get_translated_tokens(self):
        return self._translated_sents.get_all_tokens()

    def get_translated_text(self):
        return self._translated_sents.get_text()
