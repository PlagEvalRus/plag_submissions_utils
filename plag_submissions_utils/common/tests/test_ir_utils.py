#!/usr/bin/env python
# coding: utf-8

import unittest

import plag_submissions_utils.common.ir_utils  as ir_utils
from plag_submissions_utils.common.chunks  import Chunk
from plag_submissions_utils.common.chunks  import ChunkOpts


class CosSimTestCase(unittest.TestCase):

    def cos_test(self):
        opts = ChunkOpts(True)
        chunk = Chunk(u"Но в нём теперь красовалась большая пробоина, которая требовала немедленного ремонта.",
                      u"Большими усилиями команды судно удалось вытащить из мели, но в нём теперь красовалась большая пробоина, требовавшая немедленного ремонта. ",
                      "", "", 1, opts)

        # print u",".join(chunk.get_mod_tokens())
        sim = ir_utils.cos_sim(ir_utils.gen_ngrams(chunk.get_orig_tokens(), 3),
                               ir_utils.gen_ngrams(chunk.get_mod_tokens(), 3))
        self.assertLess(0.4, sim)
        # print sim

    def jac_test(self):
        opts = ChunkOpts(True)
        # opts = ChunkOpts()
        chunk = Chunk(u"Но в нём теперь красовалась большая пробоина, которая требовала немедленного ремонта.",
                      u"Большими усилиями команды судно удалось вытащить из мели, но в нём теперь красовались большие пробоины, требовавшая немедленного ремонта. ",
                      "", "", 1, opts)

        sim = ir_utils.jaccard(ir_utils.gen_ngrams(chunk.get_orig_tokens(), 1),
                               ir_utils.gen_ngrams(chunk.get_mod_tokens(), 1))
        self.assertLess(0.4, sim)

    def lev_test(self):
        # opts = ChunkOpts(True)
        opts = ChunkOpts()
        chunk = Chunk(u"Но в нём теперь красовалась большая пробоина, которая требовала немедленного ремонта.",
                      u"Большими усилиями команды судно удалось вытащить из мели, но в нём теперь красовались большие пробоины, требовавшая немедленного ремонта. ",
                      "", "", 1, opts)

        sim = 1.0 - chunk.measure_dist()
        self.assertGreater(0.3, sim)

    def lev_reordering_test(self):
        opts = ChunkOpts(True)
        # opts = ChunkOpts()
        chunk = Chunk(u"Но в нём теперь красовалась большая пробоина, которая требовала немедленного ремонта.",
                      u"Большая пробоина, которая требовала немедленного ремонта, в нём теперь красовалась. ",
                      "", "", 1, opts)

        sim = 1.0 - chunk.measure_dist()
        self.assertGreater(0.2, sim)
