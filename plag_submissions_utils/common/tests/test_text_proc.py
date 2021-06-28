#!/usr/bin/env python
# coding: utf-8

import unittest


import plag_submissions_utils.common.text_proc as text_proc


class SegTestCase(unittest.TestCase):
    def test_sent_with_trailing_spc(self):
        sent="When most people think of piracy, images of Captain Hook from the story Peter Pan and Captain Blackbeard from the movie Pirates of the Caribbean come to mind. "

        sents = text_proc.seg_text_as_list(sent)
        self.assertEqual(1, len(sents))

    def test_basic(self):
        text = "простое предложение. «второе« 1990 предложение, (и т.д.). 3-е предл."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(3, len(sents))
        self.assertEqual("простое предложение.", sents[0][0])
        self.assertEqual("«второе« 1990 предложение, (и т.д.).", sents[1][0])


    def test_year(self):
        text = "В 1982 г. перестало."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))

        text = "В 1982г. перестало."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))
        self.assertEqual("В 1982г. перестало.", sents[0][0])

    def test_abbrevs(self):
        text = "На ул. Горького в д. 9 проживает И.В. Ильич с пн. по пт."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))

    def test_joint(self):
        text = "заповеди Пифагора.Нравственные устои."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(2, len(sents))
        self.assertEqual("заповеди Пифагора.", sents[0][0])


    def test_newline_in_sent(self):
        text = "Перенос\r\nстроки\n на ул. Горь-\nкого. "
        sents = text_proc.seg_text_as_list(text)
        print(sents)
        self.assertEqual(1, len(sents))
        self.assertEqual("Перенос строки на ул. Горького.", sents[0][0])

        #text with Unicode Character 'HYPHEN'
        text = "Перенос стр\u2010\nоки."
        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))
        self.assertEqual("Перенос строки.", sents[0][0])

    def test_preproces(self):
        text = """Текст\nс пере-\nносами.
        Предложение с\tтабуляцие   и    пробелами."""

        # print(list(text_proc.seg_text(text)))
        new_text = text_proc.preprocess_text(text, split_on_paragraphs=True)
        self.assertEqual("Текст с переносами.\nПредложение с табуляцие и пробелами.\n", new_text)


    def test_parens_quotes(self):
        text = "изложены им в брошюре-манифесте (От кубизма к супрематизму. Новый живописный реализм)."

        sents = text_proc.seg_text_as_list(text)
        self.assertEqual(1, len(sents))

        # text = "изложены им в брошюре-манифесте «От кубизма к супрематизму. Новый живописный реализм»."
        # sents = text_proc.seg_text_as_list(text)
        # self.assertEqual(1, len(sents))

        #Unbalanced quote
        # text = "Последним пиком творчества была техника «абстракций» («Доминирующая кривая)."
        # sents = text_proc.seg_text_as_list(text)
        # print([s[0] for s in sents])
        # self.assertEqual(1, len(sents))

class MorphTestCase(unittest.TestCase):
    def test_morph(self):
        text = "Пришедшие люди, ушли ни с чем!"
        tokens = text_proc.tok_sent(text, normalize = True)
        # print tokens
        self.assertEqual(6, len(tokens))
        self.assertEqual('пришедший', tokens[0])
        self.assertEqual('человек', tokens[1])
        self.assertEqual('уйти', tokens[2])


    def test_skip_stop(self):
        text = "Пришедшие люди, ушли ни с чем!"
        tokens = text_proc.tok_sent(text, skip_stop_words = True)
        self.assertEqual(3, len(tokens))
        self.assertEqual('пришедший', tokens[0])
        self.assertEqual('человек', tokens[1])
        self.assertEqual('уйти', tokens[2])
