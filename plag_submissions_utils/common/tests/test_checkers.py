#!/usr/bin/env python
# coding: utf-8

import logging
import unittest
import regex

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
        opts = ProcessorOpts("data/test_data/test_orig_mod_type/sources",
                             "data/test_data/test_orig_mod_type/sources_list.xlsx")
        errors, _ = Processor(opts, self.checkers, []).check()

        self.assertEqual(2, len(errors))


class SentCorrectnessCheckerTestCase(unittest.TestCase):

    def test_term_in_the_end(self):
        checker = chks.SentCorrectnessChecker(['term_in_the_end'])
        chunk = Chunk("", "Correct sent with trailing spaces!!!!!  ", "", "", 1)
        checker(chunk, None)
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

class CyrillicAlphabetChecker(unittest.TestCase):
    def setUp(self):
        self.checker = chks.CyrillicAlphabetChecker(Opts())

    def test_regex_matching_1(self):
        chunk = Chunk([], u"Здeсь есть одна замена.", "ADD", "filename", "1")
        self.checker(chunk, None)
        self.assertEqual(1, len(self.checker.get_errors()))

    def test_regex_matching_2(self):
        chunk = Chunk([], u"Здесь замен нет.", "ADD", "filename", "1")
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))
