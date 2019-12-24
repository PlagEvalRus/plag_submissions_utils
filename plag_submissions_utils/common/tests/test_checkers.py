#!/usr/bin/env python
# coding: utf-8

import logging
import unittest
# import regex

import plag_submissions_utils.common.checkers  as chks
from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.errors import ErrSeverity

from plag_submissions_utils.v1.processor import ProcessorOpts
from plag_submissions_utils.v1.processor import Processor


class Opts(object):
    """Documentation for Opts

    """
    def __init__(self, min_dist=30):
        super(Opts, self).__init__()
        self.min_lexical_dist = min_dist


class LexicalSimCheckerTestCase(unittest.TestCase):

    def setUp(self):
        self.checker = chks.LexicalSimChecker(Opts())

    def simple_test(self):
        chunk = Chunk("Text about animals.",
                      "Text - about = animals.",
                      "LPR,ADD", "rvan'", 1)
        self.checker(chunk, None)

        errors = self.checker.get_errors()
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.HIGH, errors[0].sev)

    def simple_test2(self):
        chunk = Chunk("Text about animals in the wild.",
                      "Text - about = animals in a wild.",
                      "LPR", "rvan'", 1)
        logging.debug(chunk)
        self.checker(chunk, None)

        errors = self.checker.get_errors()
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.NORM, errors[0].sev)


class ORIGModTypeCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.checkers = [chks.ORIGModTypeChecker()]

    def test_submission(self):
        proc = Processor(ProcessorOpts(), self.checkers, [])
        errors, _ = proc.check("data/test_data/test_orig_mod_type/sources",
                               "data/test_data/test_orig_mod_type/sources_list.xlsx")

        self.assertEqual(2, len(errors))


class SentCorrectnessCheckerTestCase(unittest.TestCase):

    def test_term_in_the_end(self):
        checker = chks.SentCorrectnessChecker(['term_in_the_end'])
        chunk = Chunk("", "Correct sent with trailing spaces!!!!!  ", "", "", 1)
        checker(chunk, None)
        self.assertEqual(1, len(chunk.get_mod_sents()))
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", "Boring sent.", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", "Question mark?", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))


        chunk = Chunk("", "Without term   ", "", "", 1)
        checker(chunk, None)
        self.assertEqual(1, len(checker.get_errors()))


    def test_title_case(self):
        checker = chks.SentCorrectnessChecker(['title_case'])
        chunk = Chunk("", u"Корректное предложение!", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))


        chunk = Chunk("", u"Из-за дефиса не работает str.istitle.", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", u'"Цитата: текст"', "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", u'2009 number is ok.', "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", u"маленькая буква.", "", "", 1)
        checker(chunk, None)
        self.assertEqual(1, len(checker.get_errors()))

    def test_fix_term_in_the_end(self):
        checker = chks.SentCorrectnessChecker(['term_in_the_end'])

        chunk = Chunk("", "Without term   ", "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Without term.", chunk.get_mod_text())

        chunk = Chunk("", ["Without term  ", "wo term"], "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Without term.\nwo term.", chunk.get_mod_text())

        chunk = Chunk("", ["Boring sent.", "text"], "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Boring sent.\ntext.", chunk.get_mod_text())

    def test_fix_title_case(self):
        checker = chks.SentCorrectnessChecker(['title_case'])

        chunk = Chunk("", u"маленькая буква.", "", "", 1)
        checker.fix(chunk)
        self.assertEqual(u"Маленькая буква.", chunk.get_mod_text())

        chunk = Chunk("", u". В основном токсин из организма выводится через почки.", "", "", 1)
        checker.fix(chunk)
        self.assertEqual(1, len(chunk.get_mod_sents()))
        self.assertEqual(u"В основном токсин из организма выводится через почки.",
                         chunk.get_mod_text())


class SpellCheckerTestCase(unittest.TestCase):

    def setUp(self):
        self.checker = chks.SpellChecker()

    def test_without_typos(self):
        chunk = Chunk("", u"Этот текст точно без ошибок!", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_with_typos(self):
        chunk = Chunk("", u"я визиал и атправил вам я нарушел", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        errors = self.checker.get_errors()
        logging.debug("Errors: %s", "\n".join(str(e) for e in errors))
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.HIGH, errors[0].sev)

    def test_named_entities(self):
        chunk = Chunk("", u"не учитываем имена собственные:"\
                          u" Кишенев, Кипелов, Чубайс, МЭИ", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_eng(self):
        chunk = Chunk("", u"This is a sentence without any error!", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))


    def test_yo(self):
        chunk = Chunk("", u"также превращён в музей", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_years(self):
        chunk = Chunk("", u"В 60-ых годах началось резкое развитие", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_eng_with_typos(self):
        chunk = Chunk("", u"I failed to wite good english, shame on me!", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(1, len(self.checker.get_errors()))

    def test_tf(self):
        self.checker._typo_max_tf = 3
        chunk = Chunk("", u"Это не ашибка, это не ашибка, это не ашибка.", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_fix(self):
        text = u"Ещётакже искуССТвенно содзано биологиеское оржуие (бубоны)."
        chunk = Chunk("", text, "", "", 1)
        text2 = u"Нет ошибок"
        chunk2 = Chunk("", text2, "", "", 2)
        #NO fixes for CPY
        text3 = u"Выливные и распыливающие авиационные приборы"
        chunk3 = Chunk("", text3, "CPY", "", 1)

        self.checker.fix_all([chunk, chunk2, chunk3])
        self.assertEqual(
            u"Ещётакже искусственно создано биологическое оружие (бубоны).",
            chunk.get_mod_text())

        self.assertEqual(u"Нет ошибок", chunk2.get_mod_text())

        self.assertEqual(u"Выливные и распыливающие авиационные приборы", chunk3.get_mod_text())

    def test_whitelist(self):
        text = u"ошибкл, не ашибка."
        chunk = Chunk("", text, "", "", 1)
        checker = chks.SpellChecker(whitelist = [u"ашибка"])
        checker.fix_all([chunk])
        self.assertEqual(u"ошибка, не ашибка.", chunk.get_mod_text())



class CyrillicAlphabetChecker(unittest.TestCase):
    def setUp(self):
        self.checker = chks.CyrillicAlphabetChecker(Opts())

    def test_basic(self):
        chunk = Chunk([], u"Здесь замен нет.", "ADD", "filename", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

        chunk = Chunk([], u"Здeсь есть одна замена.", "ADD", "filename", 1)
        self.checker(chunk, None)
        self.assertEqual(1, len(self.checker.get_errors()))
        # print self.checker.get_errors()[0]


    def test_fix(self):
        chunk = Chunk("", [u"искуᏟꓚCСTвенный.", u"искуᏟꓚCСTвенный cнeг."], "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"искуССССТвенный.\nискуССССТвенный снег.", chunk.get_mod_text())

        # Tор -> first letter is latin
        chunk = Chunk("", u"Tор, HTTP-траффик", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"Тор, HTTP-траффик", chunk.get_mod_text())

        chunk = Chunk("", u"Пpoтoкoл Http; шкoлa - école.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"Протокол Http; школа - école.", chunk.get_mod_text())

        chunk = Chunk("", u"Замен нет.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"Замен нет.", chunk.get_mod_text())

        chunk = Chunk("", [u"Замен нет.", u"Зaмeны есть.", u"Замен нет."], "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"Замен нет.\nЗамены есть.\nЗамен нет.", chunk.get_mod_text())


    def test_NOT_fix_numbers(self):
        chunk = Chunk("", u"1982г.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual(u"1982г.", chunk.get_mod_text())
