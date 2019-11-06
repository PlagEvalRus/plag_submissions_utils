#!/usr/bin/env python
# coding: utf-8


from . import metrics
from .metrics import ViolationLevel

from .translated_chunks import TranslatorType
from .translated_chunks import translation_type_to_str



class AutoTranslationMetric(metrics.IMetric):
    def __init__(self, translation_type, ratio_interval,
                 fluctuation_delta = 3):
        self._translation_type = translation_type
        self._ratio_interval = ratio_interval
        self._fluctuation_delta = fluctuation_delta
        self._translation_type_ratio = 0

    def strict_mod(self):
        if self._ratio_interval[0] > self._translation_type_ratio:
            return ViolationLevel.HIGH
        if self._ratio_interval[1] < self._translation_type_ratio:
            return ViolationLevel.HIGH
        return ViolationLevel.OK

    def get_value(self):
        return self._translation_type_ratio

    def get_violation_level(self):
        if self._ratio_interval[0] <= self._translation_type_ratio <= self._ratio_interval[1]:
            return ViolationLevel.OK
        return ViolationLevel.HIGH

    def __call__(self, stat, chunks):
        translation_type_cnt = stat.translation_type_freqs[self._translation_type]
        self._translation_type_ratio = float(translation_type_cnt) / stat.chunks_cnt
        self._translation_type_ratio *= 100
        self._translation_type_ratio = round(self._translation_type_ratio, 1)

    def __str__(self):
        common = "%.1f%% предложений имеют тип перевода: %s" % (
            self.get_value(), translation_type_to_str(self._translation_type))
        if self._translation_type == TranslatorType.UNK:
            return common + " (UNK означает неизвестный тип переводчика. " \
                "Скорее всего в названии некоторых типов перевода опечатка.)"
        return common


class ModTranslationMetric(metrics.IMetric):
    def __init__(self, max_ratio, fluctuation_delta = 3):
        self._max_ratio = max_ratio
        self._fluctuation_delta = fluctuation_delta
        self._mod_translation_type_ratio = 0

    def get_value(self):
        return self._mod_translation_type_ratio

    def get_violation_level(self):
        if self._mod_translation_type_ratio > self._max_ratio:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        self._mod_translation_type_ratio = stat.unmod_translated_sents*100 / stat.chunks_cnt*100
        self._mod_translation_type_ratio /= 100

    def __str__(self):
        common = "%.1f%% предложений являются немодифицированными переводами" % (self._mod_translation_type_ratio)
        return common
