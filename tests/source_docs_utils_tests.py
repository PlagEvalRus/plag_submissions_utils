#!/usr/bin/env python
# coding: utf-8

import unittest
import plag_submissions_checker.submission_checker_utils as scu
import tempfile

class SourceDocTestCase(unittest.TestCase):
    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix = ".txt")
        tmp_file.write("""Сетевой маркетинг - история
Но для начала – немного истории СМ.

образу Нашему
[…]

Она неразрывно связана с именем
американца Карла Ренборга (1897­
1973), чьи реализованные идеи
превратились в индустрию сетевого
ТРЕШОВАЯ РЕКЛАМА

Сказка о

маркетинга с многомиллиардным

домоправител

оборотом.

ьнице и Доме

В Соединенных Штатах Америки, где

Мечты
Жил да был на

Ренборг оказался в 1927 году, он

свете мужик
Сетевой xxx дел мастер - прапорщик
        """)
        tmp_file.flush()
        self.source_doc = scu.SourceDoc(tmp_file.name)


    def simple_test(self):
        text = u"Она неразрывно связана с именем"
        self.assertTrue(self.source_doc.is_sent_in_doc(text))

    def regex_test(self):
        text = u"""Она нера- зрывно связ-
        ана с именем"""
        self.assertTrue(self.source_doc.is_sent_in_doc(text))

    def seq_matching_test(self):
        text = u"""чьи реализованные идеи
превратились в индустрию сетевого маркетинга с многомиллиардным оборотом."""
        self.assertTrue(self.source_doc.is_sent_in_doc(text))

    def non_matching_text_test(self):
        text = u"совершенно рандомный текст"
        self.assertFalse(self.source_doc.is_sent_in_doc(text))

        
    def non_matching_text_test2(self):
        text = u"начала маркетинга свете"
        self.assertFalse(self.source_doc.is_sent_in_doc(text))

    def changed_text_test(self):
        text = u"Она разрывно связана с именем"
        self.assertFalse(self.source_doc.is_sent_in_doc(text))

    def fury_test(self):
        text = u"Сетевой дел мастер - прапорщик"
        self.assertTrue(self.source_doc.is_sent_in_doc(text))
        # self.assertTrue("")


class AnotherTestCase(unittest.TestCase):
    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix = ".txt")
        tmp_file.write("""
        в соединенных штатах америки где мечты жил да был на ренборг оказался в 1927 году он свете мужик вплотную приступил к созданию тарас не то различных пищевых добавок основой чтобы для которых избрал люцерну как содержащую множество витаминов минералов белка и других полезных компонентов""")
        tmp_file.flush()
        self.source_doc = scu.SourceDoc(tmp_file.name)


    def simple_test(self):
        text = u"в соединенных штатах америки где ренборг оказался в 1927 году он вплотную приступил к созданию различных пищевых добавок основой для которых избрал люцерну содержащую множество витаминов минералов белка и других полезных компонентов"
        self.assertTrue(self.source_doc.is_sent_in_doc(text))

        
class YetAnotherTestCase(unittest.TestCase):
    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix = ".txt")
        tmp_file.write("""Тогда

бизнесе

Карл стал брать за них деньги, поняв,

возникает

что ничто бесплатное не ценится.

момент, когда""")
        tmp_file.flush()
        self.source_doc = scu.SourceDoc(tmp_file.name)


    def simple_test(self):
        text = u"Тогда Карл стал брать за них деньги, поняв, что ничто бесплатное не ценится."
        self.assertTrue(self.source_doc.is_sent_in_doc(text))
