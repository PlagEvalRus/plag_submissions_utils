#!/usr/bin/env python
# coding: utf-8

import unittest

from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.stat import StatCollector

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
