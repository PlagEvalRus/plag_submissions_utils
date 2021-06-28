#!/usr/bin/env python
# coding: utf-8

import unittest
import mock

from plag_submissions_utils.common.source_doc import SourceDoc

def dummy_doc(path):
    return """text
немного 1рашн1 текст.
Sentence for 'simple' test!

Text text text!

Sentence for hyp-
hen test!


Text.
Предложение для проверки <trash> sequence matcher <trash> test!
Sentence for <many trash> sequence matcher <many trash> test!
"""

SIMPLE_SENT="Sentence for 'simple' test!"
SEQ_MATCHER_SENT="Предложение для проверки sequence matcher test!"
SEQ_MATCHER_SENT2="Sentence for hyphen test!"

class FindSentInSrcTestCase(unittest.TestCase):

    @mock.patch("plag_submissions_utils.common.text_proc.convert_doc",
                dummy_doc)
    def setUp(self):
        self.source_doc = SourceDoc("/dev/null",
                                    max_offs_delta=30)

    def test_simple_case(self):
        self.assertTrue(self.source_doc.is_sent_in_doc(SIMPLE_SENT))

    def test_hyphen_case(self):
        self.assertTrue(self.source_doc.is_sent_in_doc(SEQ_MATCHER_SENT2))

    def test_seq_matcher_case(self):
        self.assertTrue(self.source_doc.is_sent_in_doc(SEQ_MATCHER_SENT))


    def test_seq_matcher_case2(self):
        text = "немного 1рашн1 текст simple'"
        self.assertTrue(self.source_doc.is_sent_in_doc(text))

    def test_limit_of_seq_matcher(self):
        #'<many trash>'  is in the end of the source_doc
        text = "немного 1рашн1 текст <many trash>"
        self.assertFalse(self.source_doc.is_sent_in_doc(text))

    def test_offs_simple_case(self):
        offs_beg, offs_end, err = self.source_doc.get_sent_offs(SIMPLE_SENT)

        self.assertEqual(27, offs_beg)
        self.assertEqual(54, offs_end)
        self.assertEqual(0, err)

        self.assertEqual(SIMPLE_SENT, self.source_doc.get_text()[offs_beg:offs_end])

    def test_offs_hyphen_case(self):
        offs_beg, offs_end, err = self.source_doc.get_sent_offs(SEQ_MATCHER_SENT2)

        self.assertEqual(73, offs_beg)
        self.assertEqual(98, offs_end)
        self.assertEqual(0, err)

        assert "Sentence for hyphen test!" == self.source_doc.get_text()[offs_beg:offs_end]

    def test_offs_seq_matcher(self):
        offs_beg, offs_end, err = self.source_doc.get_sent_offs(SEQ_MATCHER_SENT)

        self.assertEqual(106, offs_beg)
        self.assertEqual(169, offs_end)
        self.assertEqual(16, err)

        print(self.source_doc.get_text())
        self.assertEqual("Предложение для проверки <trash> sequence matcher <trash> test!",
                         self.source_doc.get_text()[offs_beg:offs_end])


    @mock.patch("plag_submissions_utils.common.text_proc.convert_doc",
                dummy_doc)
    def test_offs_with_large_delta(self):

        source_doc = SourceDoc("/dev/null",
                               max_offs_delta=180)
        offs_beg, offs_end, err = source_doc.get_sent_offs(
            SEQ_MATCHER_SENT)

        self.assertEqual(106, offs_beg)
        self.assertEqual(169, offs_end)
        self.assertEqual(16, err)

        self.assertEqual("Предложение для проверки <trash> sequence matcher <trash> test!",
                         source_doc.get_text()[offs_beg:offs_end])


    @unittest.skip("current limitation")
    def test_offs_with_repeated_parts(self):
        #It finds the first occurrence of a part
        #that is repeated many times in the text: ' sequence matcher '
        offs_beg, offs_end, err = self.source_doc.get_sent_offs(
            "Sentence for sequence matcher test!")

        self.assertEqual(173, offs_beg)
        self.assertEqual(242, offs_end)
        self.assertEqual(26, err)

        self.assertEqual("Sentence for <many trash> sequence matcher <many trash> test!",
                         dummy_doc("temp")[offs_beg:offs_end])


def make_doc_from_txt(text):
    return text

class SpecificSeqMatcherCases(unittest.TestCase):

    @mock.patch("plag_submissions_utils.common.text_proc.convert_doc",
                make_doc_from_txt)
    def create_source_doc(self, text, offs_delta = 160):
        return SourceDoc(text, max_offs_delta=offs_delta)

    def test1(self):
        #Fixed by adding max_length_delta = 4 to SourceDoc
        text = "В 7разрядной и 8разрядной кодировки ASCII."

        src_doc = self.create_source_doc(text)

        sent = """В 7 разрядной и 8 разрядной кодировки ASCII."""

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(0, offs_beg)
        self.assertEqual(2, err)

    def test2(self):
        #leading whitespace in sent
        #bun it is absent in text
        #Fixed by adding strip() to received sent in get_sent_offs
        text = """приблизительно неделю.

В этом году вышел релиз версии 2.0 Pebble SDK, наряду
"""

        sent = """ В этом году вышел релиз версии 2.0 Pebble SDK, наряду
"""
        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(24, offs_beg)
        self.assertEqual(77, offs_end)
        self.assertEqual(0, err)

    def test3(self):
        #fixed by replacing non-breaking spaces in src and sent
        text = """косметических
(Oriflame, Avon, Faberlic, Mary Kay) и медицинских"""

        sent = """косметических
(Oriflame, Avon, Faberlic, Mary Kay) и медицинских"""

        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(0, offs_beg)
        self.assertEqual(64, offs_end)
        self.assertEqual(0, err)

    def test4(self):
        #fixed by replacing unicode hyphens (\u2010) with simple ones (\u002d)
        text = """Сетевые продажи (Multilevel Marketing ‐ MLM) ‐ такой способ ‐‐‐
"""
        sent = """Сетевые продажи (Multilevel Marketing - MLM) - такой способ ---
"""
        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(0, offs_beg)
        self.assertEqual(63, offs_end)
        self.assertEqual(0, err)

    def test5(self):
        #fixed by removing double spaces in src text
        text = """Другой текст... обязательно другой текст....
бизнеса. Не  обязательно  сам  участник  бизнеса  должен  привлекать  других
участников."""
        sent = """Не обязательно сам участник бизнеса должен привлекать других участников."""
        src_doc = self.create_source_doc(text, 4)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(54, offs_beg)
        # 7 double whitespaces will be deleted
        self.assertEqual(133 - 7, offs_end)
        self.assertEqual(0, err)
        self.assertEqual(sent, src_doc.get_text()[54:133-7])

    def test6(self):
        text = """Информация о полезных добавках
получила широкое распространение
(у каждого из знакомых Ренборга
нашлось много своих знакомых),
люди просили Ренборга о встречах,

"Как Сказку
сделать
Былью":
Отзывы

чтобы получить больше информации о
новом продукте.
"""

        sent= """Информация о полезных добавках получила широкое распространение (у каждого из знакомых Ренборга нашлось много своих знакомых), люди просили Ренборга о встречах, чтобы получить больше информации о новом продукте.
"""


        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(0, offs_beg)
        self.assertEqual(248, offs_end)
        self.assertEqual(38, err)

    def test7(self):
        text = """Пред1 Конец1.
Пред2..."""

        sent= """. Пред2.."""


        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        print(err)
        self.assertEqual("Пред2..", src_doc.get_text()[offs_beg:offs_end])

    def test8(self):
        text = """Коби
        сент
        сент
        сент
        Коб Брайант присоединился к «Лос-Анджелес Лейкерз» в 1996, став играть вместе с центровым Шакилом О’Нил."""

        sent = "Коби Брайант присоединился к «Лос-Анджелес Лейкерз» в 1996, став играть вместе с центровым Шакилом О’Нил."
        src_doc = self.create_source_doc(text)

        offs_beg, offs_end, err = src_doc.get_sent_offs(sent)
        self.assertEqual(0, offs_beg)
        self.assertEqual(len(src_doc.get_text())-1, offs_end)
