#!/usr/bin/env python
# coding: utf-8

from .translated_chunks import TranslatorType
from . import checkers as chks
from .checkers import ChunkError
from .checkers import ErrSeverity

from .translator import YaGoTrans

class ORIGModTypeChecker(chks.ORIGModTypeChecker):
    def _should_run(self, chunk):
        return chunk.get_translator_type() == TranslatorType.ORIGINAL


class TranslationChecker(chks.IChecher):
    def __init__(self, opts):
        super(TranslationChecker, self).__init__()
        self._trans = YaGoTrans()
        self._errors = []

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):
        if chunk.get_translator_type() == TranslatorType.GOOGLE or chunk.get_translator_type() == TranslatorType.YANDEX:
            try:
                if ' '.join(chunk.get_translated_sents()).encode('utf-8') is self._trans.translate(' '.join(chunk.get_orig_sents()), translator=chunk.get_translator_type_str()):
                    self._errors.append(
                        ChunkError("Переведенный текст не соответствует переводу, получаемому с помощью заявленного переводчика!",
                                   chunk.get_chunk_id(),
                                   ErrSeverity.HIGH))
            except IndexError:
                pass


class ManualTranslationChecker(chks.IChecher):
    def __init__(self, opts):
        super(ManualTranslationChecker, self).__init__()
        self._trans = YaGoTrans()
        self._errors = []

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):
        if chunk.get_translator_type() == TranslatorType.MANUAL and chunk.get_orig_sents():
            if ' '.join(chunk.get_mod_sents()).encode('utf-8') == self._trans.translate(chunk.get_orig_sents()[0],
                                                                                        translator='yandex'):
                self._errors.append(
                    ChunkError(
                        "Текст, заявленный как переведенный вручную, переведён Яндекс Переводчиком!",
                        chunk.get_chunk_id(),
                        ErrSeverity.HIGH))
            elif ' '.join(chunk.get_mod_sents()).encode('utf-8') == self._trans.translate(chunk.get_orig_sents()[0],
                                                                                        translator='google'):
                self._errors.append(
                    ChunkError(
                        "Текст, заявленный как переведенный вручную, переведён Google Translate!",
                        chunk.get_chunk_id(),
                        ErrSeverity.HIGH))
            else:
                pass
