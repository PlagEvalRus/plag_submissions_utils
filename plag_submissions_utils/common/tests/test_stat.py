#!/usr/bin/env python
# coding: utf-8

import unittest
import itertools

from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.stat import StatCollector
from plag_submissions_utils.common.stat import SrcStatCollector

class StatTestCase(unittest.TestCase):

    def test_co_occ(self):
        chunks = [
            Chunk("", "", "ADD,DEL,SYN", "", 1),
            Chunk("", "", "ADD", "", 2),
            Chunk("", "", "ADD,HPR", "", 3),
            Chunk("", "", "ADD,DEL", "", 4),
            Chunk("", "", "SYN,DEL,HPR,LPR", "", 5),
            Chunk("", "", "ADD,DEL,SYN,LPR", "", 6)

        ]
        collector = StatCollector()
        collector(chunks[0:2])
        collector(chunks[2:])
        stat = collector.get_stat()


        self.assertEqual(5, len(stat.mod_type_freqs))
        self.assertEqual(5, stat.mod_type_freqs[ModType.ADD])
        self.assertEqual(3, stat.mod_type_freqs[ModType.SYN])

        self.assertEqual(3, stat.mod_type_co_occur[(ModType.DEL, ModType.ADD)])
        self.assertEqual(3, stat.mod_type_co_occur[(ModType.DEL, ModType.SYN)])
        self.assertEqual(2, stat.mod_type_co_occur[(ModType.DEL, ModType.ADD, ModType.SYN)])
        self.assertEqual(2, stat.mod_type_co_occur[(ModType.LPR, ModType.DEL, ModType.SYN)])


    def test_src_stat(self):
        all_chunks = [
            [
                [Chunk("", "", "ADD", "src1", i) for i in range(0,20)],
                [Chunk("", "", "DEL", "src2", i) for i in range(0,15)],
                [Chunk("", "", "DEL", "src3", i) for i in range(0,4)]
            ],
            [
                [Chunk("", "", "DEL", "src4", i) for i in range(0,46)],
                [Chunk("", "", "DEL", "src5", i) for i in range(0,123)],
                [Chunk("", "", "DEL", "src6", i) for i in range(0,5)],
                [Chunk("", "", "DEL", "src7", i) for i in range(0,29)]
            ]
        ]

        collector = SrcStatCollector()
        for chunks in all_chunks:
            collector(itertools.chain(*chunks))

        docs_cnt_stat, sents_in_src_stat = collector.get_stat()


        self.assertEqual(2, len(docs_cnt_stat))
        self.assertEqual(1, docs_cnt_stat[3])
        self.assertEqual(1, docs_cnt_stat[4])

        self.assertEqual(5, len(sents_in_src_stat))
        self.assertEqual(2, sents_in_src_stat[0])
        self.assertEqual(1, sents_in_src_stat[1])
        self.assertEqual(2, sents_in_src_stat[2])
        self.assertEqual(1, sents_in_src_stat[4])
        self.assertEqual(1, sents_in_src_stat[10])
