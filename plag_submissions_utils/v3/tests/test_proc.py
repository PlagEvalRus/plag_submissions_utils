#!/usr/bin/env python
# coding: utf-8

import unittest

import plag_submissions_utils.common_runner as runner
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.translated_chunks import TranslatorType

class ProcessorTestCase(unittest.TestCase):

    def _process_file(self, archive_path):
        return runner.run(archive_path, "3")

    def test_file(self):
        metrics, errors, stat = self._process_file("data/test_data_v3/test.zip")


        print(stat)
        self.assertEqual(3, len(errors), "errors:\n%s" % '\n'.join(str(e) for e in errors))
        self.assertEqual(8, stat.chunks_cnt)

        self.assertEqual(0, stat.mod_type_freqs[ModType.UNK])
        self.assertEqual(4, stat.mod_type_freqs[ModType.ORIG])
        self.assertEqual(4, stat.mod_type_freqs[ModType.DEL])

        self.assertEqual(1, stat.translation_type_freqs[TranslatorType.GOOGLE])
        self.assertEqual(3, stat.translation_type_freqs[TranslatorType.YANDEX])
        self.assertEqual(2, stat.translation_type_freqs[TranslatorType.ORIGINAL])
        self.assertEqual(2, stat.translation_type_freqs[TranslatorType.MANUAL])

        self.assertEqual(3, stat.docs_freqs["elvis_wiki"])
        self.assertEqual(3, stat.docs_freqs["ElvisIMDb"])

        # self.assertEqual(1, _metrics_violations_cnt(
        #     metrics, ViolationLevel.HIGH))
