#!/usr/bin/env python
# coding: utf-8

import logging
import unittest


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

    def test_simple(self):
        chunk = Chunk("Text about animals.",
                      "Text - about = animals.",
                      "LPR,ADD", "rvan'", 1)
        self.checker(chunk, None)

        errors = self.checker.get_errors()
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.HIGH, errors[0].sev)

    def test_simple2(self):
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
        chunk = Chunk("", "Корректное предложение!", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))


        chunk = Chunk("", "Из-за дефиса не работает str.istitle.", "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", '"Цитата: текст"', "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", '2009 number is ok.', "", "", 1)
        checker(chunk, None)
        self.assertEqual(0, len(checker.get_errors()))

        chunk = Chunk("", "маленькая буква.", "", "", 1)
        checker(chunk, None)
        self.assertEqual(1, len(checker.get_errors()))

    def test_fix_term_in_the_end(self):
        checker = chks.SentCorrectnessChecker(['term_in_the_end'])

        chunk = Chunk("", "Without term   ", "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Without term.", chunk.get_mod_text())

        chunk = Chunk("", ["Without term  ", "wo term"], "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Without term. wo term.", chunk.get_mod_text())

        chunk = Chunk("", ["Boring sent.", "text"], "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Boring sent. text.", chunk.get_mod_text())

    def test_fix_title_case(self):
        checker = chks.SentCorrectnessChecker(['title_case'])

        chunk = Chunk("", "маленькая буква.", "", "", 1)
        checker.fix(chunk)
        self.assertEqual("Маленькая буква.", chunk.get_mod_text())

        chunk = Chunk("", ". В основном токсин из организма выводится через почки.", "", "", 1)
        checker.fix(chunk)
        self.assertEqual(1, len(chunk.get_mod_sents()))
        self.assertEqual("В основном токсин из организма выводится через почки.",
                         chunk.get_mod_text())


class SpellCheckerTestCase(unittest.TestCase):

    def setUp(self):
        self.checker = chks.SpellChecker()

    def test_without_typos(self):
        chunk = Chunk("", "Этот текст точно без ошибок!", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_with_typos(self):
        chunk = Chunk("", "я визиал и атправил вам я нарушел", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        errors = self.checker.get_errors()
        logging.debug("Errors: %s", "\n".join(str(e) for e in errors))
        self.assertEqual(1, len(errors))
        self.assertEqual(ErrSeverity.HIGH, errors[0].sev)

    def test_named_entities(self):
        chunk = Chunk("", "не учитываем имена собственные:"\
                          " Кишенев, Кипелов, Чубайс, МЭИ", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_eng(self):
        chunk = Chunk("", "This is a sentence without any error!", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))


    def test_yo(self):
        chunk = Chunk("", "также превращён в музей", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_years(self):
        chunk = Chunk("", "В 60-ых годах началось резкое развитие", "", "", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_eng_with_typos(self):
        chunk = Chunk("", "I failed to wite good english, shame on me!", "", "", 1)
        logging.debug(chunk)
        self.checker(chunk, None)
        self.assertEqual(1, len(self.checker.get_errors()))

    def test_tf(self):
        self.checker._typo_max_tf = 5
        chunk = Chunk("", "Это не ашибка, это не ашибка, это не ашибка", "", "", 1)
        chunk_cpy = Chunk("", "Это не ашибка, это не ашибка, это не ашибка", "CPY", "", 2)

        logging.debug(chunk)
        self.checker(chunk, None)
        self.checker(chunk_cpy, None)
        self.assertEqual(0, len(self.checker.get_errors()))

    def test_fix(self):
        text = "Ещётакже искуССТвенно содзано биологиеское оржуие (бубоны)."
        chunk = Chunk("", text, "", "", 1)
        text2 = "Нет ошибок"
        chunk2 = Chunk("", text2, "", "", 2)
        #NO fixes for CPY
        text3 = "Выливные и распыливающие авиационные приборы"
        chunk3 = Chunk("", text3, "CPY", "", 1)

        self.checker.fix_all([chunk, chunk2, chunk3])
        self.assertEqual(
            "Ещётакже искусственно создано биологическое оружие (бубоны).",
            chunk.get_mod_text())

        self.assertEqual("Нет ошибок", chunk2.get_mod_text())

        self.assertEqual("Выливные и распыливающие авиационные приборы", chunk3.get_mod_text())

    def test_whitelist(self):
        text = "ошибкл, не ашибка."
        chunk = Chunk("", text, "", "", 1)
        checker = chks.SpellChecker(whitelist = ["ашибка"])
        checker.fix_all([chunk])
        self.assertEqual("ошибка, не ашибка.", chunk.get_mod_text())


    def test_abbr(self):
        text = "(совр. Гаити)"
        chunk = Chunk("", text, "", "", 1)
        self.checker.fix_all([chunk])
        self.assertEqual("(совр. Гаити)", chunk.get_mod_text())

    def test_wiki(self):
        text = "Уи́льям Си́дни - тонкий"
        chunk = Chunk("", text, "", "", 1)
        self.checker.fix_all([chunk])
        self.assertEqual("Уи́льям Си́дни - тонкий", chunk.get_mod_text())



class CyrillicAlphabetChecker(unittest.TestCase):
    def setUp(self):
        self.checker = chks.CyrillicAlphabetChecker(Opts())

    def test_basic(self):
        chunk = Chunk([], "Здесь замен нет.", "ADD", "filename", 1)
        self.checker(chunk, None)
        self.assertEqual(0, len(self.checker.get_errors()))

        chunk = Chunk([], "Здeсь есть одна замена.", "ADD", "filename", 1)
        self.checker(chunk, None)
        self.assertEqual(1, len(self.checker.get_errors()))
        # print self.checker.get_errors()[0]


    def test_fix(self):
        chunk = Chunk("", ["искуᏟꓚCСTвенный.", "искуᏟꓚCСTвенный cнeг."], "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("искуССССТвенный. искуССССТвенный снег.", chunk.get_mod_text())

        # Tор -> first letter is latin
        chunk = Chunk("", "Tор, HTTP-траффик", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("Тор, HTTP-траффик", chunk.get_mod_text())

        chunk = Chunk("", "Пpoтoкoл Http; шкoлa - école.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("Протокол Http; школа - école.", chunk.get_mod_text())

        chunk = Chunk("", "Замен нет.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("Замен нет.", chunk.get_mod_text())

        chunk = Chunk("", ["Замен нет.", "Зaмeны есть.", "Замен нет."], "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("Замен нет. Замены есть. Замен нет.", chunk.get_mod_text())


    def test_NOT_fix_numbers(self):
        chunk = Chunk("", "1982г.", "", "", 1)
        self.checker.fix(chunk)
        self.assertEqual("1982г.", chunk.get_mod_text())

def test_source_docs_checker_basic(fs):
    src_dir = '/test/sources/'
    fs.create_dir(src_dir)
    fs.create_file(src_dir + "1.html")
    fs.create_file(src_dir + "wiki.html")
    fs.create_file(src_dir + "lenovo")
    fs.create_file(src_dir + "я_рюзский.pdf")

    checker = chks.SourceDocsChecker(None, src_dir)
    chunk = Chunk("", "", "", "1", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "1.html", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "wiki.html", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "wiki", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "lenovo", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "lenovo.html", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "я_рюзский.pdf", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "я_рюзский", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "я_рюзский.txt", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "2.html", 1)
    checker(chunk, None)
    assert len(checker.get_errors()) == 1

def test_source_docs_checker_with_whitespace(fs):
    src_dir = '/test/sources/'
    fs.create_dir(src_dir)
    fs.create_file(src_dir + "title kek.html")
    fs.create_file(src_dir + "знакомый ваш.html")

    checker = chks.SourceDocsChecker(None, src_dir)

    chunk = Chunk("", "", "", "title kek", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "title kek.html", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "знакомый ваш", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "знакомый ваш", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "знакомый ваш.html", 1)
    checker(chunk, None)
    assert not checker.get_errors()

def test_with_dot_and_space_in_the_end(fs):
    src_dir = '/test/sources/'
    fs.create_dir(src_dir)
    fs.create_file(src_dir + "знакомый.ваш.html")

    checker = chks.SourceDocsChecker(None, src_dir)

    chunk = Chunk("", "", "", "знакомый.ваш.html ", 1)
    checker(chunk, None)
    assert not checker.get_errors()

    chunk = Chunk("", "", "", "знакомый.ваш ", 1)
    checker(chunk, None)
    assert not checker.get_errors()


def test_with_wrong_ext(fs):
    src_dir = '/test/sources/'
    fs.create_dir(src_dir)
    fs.create_file(src_dir + "test.hmtl")

    checker = chks.SourceDocsChecker(None, src_dir)

    chunk = Chunk("", "", "", "test.hmtl", 1)
    checker(chunk, None)
    assert not checker.get_errors()
