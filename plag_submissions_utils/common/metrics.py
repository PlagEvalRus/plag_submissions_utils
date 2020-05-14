#!/usr/bin/env python
# coding: utf-8

import logging

from .chunks import ModType
from .chunks import mod_type_to_str

class ViolationLevel(object):
    OK = 0
    MEDIUM = 1
    HIGH = 2
    FATAL = 3

class IMetric(object):
    """Documentation for IMetric

    """

    def get_value(self):
        raise NotImplementedError("should implement this!")

    def get_violation_level(self):
        raise NotImplementedError("should implement this!")

    def __call__(self, stat, chunks):
        raise NotImplementedError("should implement this!")

class SrcDocsCountMetric(IMetric):
    def __init__(self, min_docs_cnt, min_sent_per_src,
                 acceptance_perc = 0.6):
        self._min_docs_cnt     = min_docs_cnt
        self._min_sent_per_src = min_sent_per_src
        self._acceptance_perc  = acceptance_perc
        self._docs_cnt         = 0

    def get_value(self):
        return self._docs_cnt

    def get_violation_level(self):
        if round(self._min_docs_cnt * self._acceptance_perc) >= self._docs_cnt:
            return ViolationLevel.FATAL

        if self._min_docs_cnt > self._docs_cnt:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        self._docs_cnt = sum(1 for k in stat.docs_freqs if stat.docs_freqs[k] >= self._min_sent_per_src)

    def __str__(self):
        return "Количество документов-источников, из которых взято"\
            " более %d предложений : %d" % (self._min_sent_per_src,
                                            self._docs_cnt)

class SentsCountMetric(IMetric):
    def __init__(self, min_real_sent_cnt, min_sent_size,
                 fluctuation_delta = 10,
                 acceptance_perc = 0.8):
        self._min_real_sent_cnt = min_real_sent_cnt
        self._min_sent_size     = min_sent_size
        self._fluctuation_delta = fluctuation_delta
        self._acceptance_perc   = acceptance_perc
        self._real_sent_cnt     = 0

    def get_value(self):
        return self._real_sent_cnt

    def get_violation_level(self):
        if round(self._min_real_sent_cnt * self._acceptance_perc) > self._real_sent_cnt:
            return ViolationLevel.FATAL

        if self._min_real_sent_cnt > self._real_sent_cnt:
            if self._min_real_sent_cnt <= \
               self._real_sent_cnt + self._fluctuation_delta:
                return ViolationLevel.MEDIUM
            else:
                return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        raise NotImplementedError("should implement SentsCountMetric.__call__")

    def __str__(self):
        raise NotImplementedError("should implement SentsCountMetric.__str__")


class DocSizeMetric(SentsCountMetric):
    def __init__(self, min_real_sent_cnt, min_sent_size,
                 fluctuation_delta = 10,
                 acceptance_perc = 0.8):
        super(DocSizeMetric, self).__init__(min_real_sent_cnt, min_sent_size,
                                            fluctuation_delta, acceptance_perc)


    def __call__(self, stat, chunks):
        self._real_sent_cnt = sum(1 for t in stat.mod_sent_lengths if t[1] > self._min_sent_size)

    def __str__(self):
        return "Количество предложений, размер которых превышает %d слов: %d" % (
            self._min_sent_size, self._real_sent_cnt)

class SrcSentsCountMetric(SentsCountMetric):
    def __init__(self, min_real_sent_cnt, fluctuation_delta = 10,
                 acceptance_perc = 0.8):
        super(SrcSentsCountMetric, self).__init__(min_real_sent_cnt, 0,
                                                  fluctuation_delta, acceptance_perc)

    def __call__(self, stat, chunks):
        self._real_sent_cnt += stat.src_sents_cnt

    def __str__(self):
        return "Количество использованных из источников предложений: %d" % self._real_sent_cnt


class ModTypeRatioMetric(IMetric):
    def __init__(self, mod_type, ratio_interval,
                 fluctuation_delta = 3):
        self._mod_type      = mod_type
        self._ratio_interval = ratio_interval
        self._fluctuation_delta = fluctuation_delta
        self._mod_type_ratio = 0

    def get_value(self):
        return self._mod_type_ratio

    def strict_mod(self):
        if self._ratio_interval[0] > self._mod_type_ratio:
            return ViolationLevel.HIGH
        elif self._ratio_interval[1] < self._mod_type_ratio:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def get_violation_level(self):
        if self._mod_type_ratio != 0 and \
           self._mod_type == ModType.UNK:
            return ViolationLevel.HIGH

        if self._mod_type_ratio == 0 and \
           self._mod_type != ModType.UNK and \
           self._mod_type != ModType.CPY and \
           self._mod_type != ModType.ORIG:
            return ViolationLevel.HIGH

        if self._mod_type == ModType.CPY:
            return self.strict_mod()

        # all other modes are
        #non strict (there may be some fluctuations from required interval)
        logging.debug("mod type %d, %s %f", self._mod_type,
                      self._ratio_interval, self._mod_type_ratio)
        if self._mod_type_ratio < self._ratio_interval[0]:
            if self._mod_type_ratio + self._fluctuation_delta >= \
               self._ratio_interval[0]:
                return ViolationLevel.MEDIUM
            else:
                return ViolationLevel.HIGH
        elif self._ratio_interval[1] < self._mod_type_ratio:
            return ViolationLevel.MEDIUM
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        mod_type_cnt = stat.mod_type_freqs[self._mod_type]
        self._mod_type_ratio = float(mod_type_cnt) / stat.chunks_cnt
        self._mod_type_ratio *= 100
        self._mod_type_ratio = round(self._mod_type_ratio, 1)

    def __str__(self):
        common = "%.1f%% предложений имеют тип: %s" % (
            self.get_value(), mod_type_to_str(self._mod_type))
        if self._mod_type == ModType.UNK:
            return common + " (UNK означает неизвестный тип сокрытия. "\
                "Скорее всего в названии некоторых типов сокрытий опечатка.)"
        return common

class MeanSentLenMetric(IMetric):
    def __init__(self, min_mean_sent_len, fluctuation_delta = 3):
        self._min_mean_sent_len = min_mean_sent_len
        self._fluctuation_delta = fluctuation_delta
        self._mean_sent_len = 0

    def get_value(self):
        return self._mean_sent_len

    def get_violation_level(self):
        if self._mean_sent_len < self._min_mean_sent_len:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        self._mean_sent_len = sum(t[1] for t in stat.mod_sent_lengths) / float(len(stat.mod_sent_lengths))

    def __str__(self):
        common = "Средняя длина предложения составляет %f слов" % (self._mean_sent_len)
        return common
