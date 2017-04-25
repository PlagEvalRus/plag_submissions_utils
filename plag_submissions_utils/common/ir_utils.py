#!/usr/bin/env python
# coding: utf-8

"""Some information retrieval utils!
"""
import csv
import math
import logging
import operator
import itertools
from collections import Counter
from collections import defaultdict

import distance

from plag_submissions_utils import common_runner
from .submissions import run_over_submissions
from .chunks import ModType
from .chunks import mod_type_to_str
from .chunks import _create_mod_type

def gen_ngrams(tokens, n = 3):
    return zip(*[tokens[i:] for i in range(n)])

def _dot_product2(v1, v2):
    return sum(map(operator.mul, v1, v2))

def _log_vec(msg, v):
    logging.debug(u"cos_sim %s: %s", msg,
                  u'\n'.join(u"%s: %d" % (u",".join(ngram), cnt) for ngram, cnt in v.most_common()))


def cos_sim(ng1, ng2):
    v1 = Counter(ng1)
    v2 = Counter(ng2)
    _log_vec("v1", v1)
    _log_vec("v2", v2)

    if not v1 or not v2:
        return 0.0

    len1 = math.sqrt(_dot_product2(v1.itervalues(), v1.itervalues()))
    len2 = math.sqrt(_dot_product2(v2.itervalues(), v2.itervalues()))

    total = 0.0
    for ngram in v1:
        if ngram in v2:
            total += v1[ngram] * v2[ngram]

    return total / (len1 * len2)

def jaccard(ng1, ng2):
    return 1.0 - distance.jaccard(ng1, ng2)

def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    N.sort()
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

class BasicSimProcessor(object):
    def __init__(self, name):
        super(BasicSimProcessor, self).__init__()
        self._name = name
        self._sims = []
        self._sims_per_type = defaultdict(lambda : [])

    def name(self):
        return self._name

    def __call__(self, chunks):
        for chunk in chunks:
            if chunk.get_mod_type() == ModType.ORIG:
                continue
            sim = self._calc_sim(chunk)
            self._sims.append(sim)
            for mod_type in chunk.get_all_mod_types():
                if mod_type != ModType.UNK:
                    self._sims_per_type[mod_type].append(sim)

    def _calc_sim(self, chunk):
        raise NotImplementedError("!!")

    def _get_percentiles(self, sims):
        return [percentile(sims, p) for p in [0.25, 0.5, 0.75] ]

    def results(self):
        return self._get_percentiles(self._sims)

    def results_per_type(self):
        return {k: self._get_percentiles(v) for k,v in self._sims_per_type.iteritems()}

    def get_sims(self):
        return self._sims

    def get_sims_by_types(self):
        return self._sims_per_type

class BasicNGramSimProcessor(BasicSimProcessor):
    def __init__(self, name, sim_func, ngram = 3):
        super(BasicNGramSimProcessor, self).__init__(name)
        self._ngram    = ngram
        self._sim_func = sim_func

    def get_ngram(self):
        return self._ngram

    def _calc_sim(self, chunk):
        return self._sim_func(gen_ngrams(chunk.get_orig_tokens(), self._ngram),
                              gen_ngrams(chunk.get_mod_tokens(), self._ngram))


class EditDistSimProcessor(BasicSimProcessor):
    def __init__(self, name):
        super(EditDistSimProcessor, self).__init__(name)

    def _calc_sim(self, chunk):
        return 1.0 - chunk.measure_dist()

def calc_sims(opts, procs):
    def proc_arc(susp_id, _, meta_file_path):
        chunks, _ = common_runner.create_chunks(
            susp_id, meta_file_path, opts = opts)
        for proc in procs:
            proc(chunks)

    run_over_submissions(opts.archive_dir, proc_arc)

def calc_cos_sim(opts):
    proc = BasicNGramSimProcessor('cos', cos_sim)

    calc_sims(opts, [proc])

    print proc.results()
    print "\n".join("%s: %s" % (mod_type_to_str(t), s)
                    for t,s in proc.results_per_type().iteritems())

def calc_jaccard_sim(opts):
    proc = BasicNGramSimProcessor('jaccard', jaccard)

    calc_sims(opts, [proc])

    print proc.results()
    print "\n".join("%s: %s" % (mod_type_to_str(t), s)
                    for t,s in proc.results_per_type().iteritems())


def calc_impact_of_morph(opts):

    def run_calc(local_opts, writer, run_tag):
        procs = [EditDistSimProcessor("lev"),
                 BasicNGramSimProcessor("jaccard", jaccard, 1)]

        calc_sims(local_opts, procs)

        rows = itertools.izip(*[p.get_sims() for p in procs])
        for row in rows:
            writer.writerow(row + (run_tag, ))


    measures = ['lev', 'jaccard']
    with open('morph_imp.csv', 'w') as csvfile:
        fieldnames = measures + ['run_tag']
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)

        #at first run without morph
        opts.normalize = False
        opts.skip_stop_words = False
        run_calc(opts, writer, "nomorph")

        #than enable morph
        opts.normalize = True
        run_calc(opts, writer, "morph")

        #than skip stop-words as well
        opts.skip_stop_words = True
        run_calc(opts, writer, "morph_nostops")

def _write_sim_by_types(filename, procs):
    mod_types = ['add', 'del', 'lpr', 'hpr', 'cct', 'ssp', 'shf', 'sep', 'syn']
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(mod_types + ['ngram'])
        for proc in procs:
            rows = itertools.izip_longest(
                *[proc.get_sims_by_types()[_create_mod_type(t)]
                  for t in mod_types])
            for row in rows:
                writer.writerow(row + (proc.name(), ))



def calc_for_various_ngrams(opts):
    ngrams = range(1,9)
    procs = [BasicNGramSimProcessor(str(ng), cos_sim, ng) for ng in ngrams]
    calc_sims(opts, procs)
    with open('cos_ngrams.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(ngrams)
        rows = itertools.izip(*[p.get_sims() for p in procs])
        for row in rows:
            writer.writerow(row)
    _write_sim_by_types('cos_ngrams_by_type.csv', procs)


def calc_various_similarity(opts):
    # calc_impact_of_morph(opts)
    calc_for_various_ngrams(opts)
    # calc_cos_sim(opts)
    # calc_jaccard_sim(opts)
