#!/usr/bin/env python
# coding: utf-8

import logging

from segtok import segmenter
import regex

from . import source_doc
from . import chunks
from .chunks import ModType
from .errors import ErrSeverity
from .errors import ChunkError
from .errors import Error
from .simple_detector import calc_originality



class IChecher(object):
    def get_errors(self):
        raise NotImplementedError("should implement this!")

    def __call__(self, chunk, src_docs):
        raise NotImplementedError("should implement this!")


class BaseChunkSimChecker(IChecher):
    def __init__(self, opts, fluctuation_delta = 3):
        self._opts              = opts
        self._diff_perc_dict    = opts.diff_perc
        self._fluctuation_delta = fluctuation_delta
        self._errors            = []

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() == ModType.ORIG:
            return


        diff_perc = chunk.measure_dist()
        diff_perc *= 100

        logging.debug("BaseChunkSimChecker: for sent %d: %f ", chunk.get_chunk_id(), diff_perc)

        error_level = None
        etal_diff_perc_tuple = self._diff_perc_dict[chunk.get_mod_type()]
        if diff_perc < etal_diff_perc_tuple[0]:
            msg = "малы"
            if diff_perc + self._fluctuation_delta >= \
               etal_diff_perc_tuple[0]:
                error_level = ErrSeverity.LOW
            elif diff_perc < 3:
                error_level = ErrSeverity.HIGH
            else:
                error_level = ErrSeverity.NORM
        elif etal_diff_perc_tuple[1] < diff_perc:
            msg = "слишком велики"
            if etal_diff_perc_tuple[1] >= \
               diff_perc - self._fluctuation_delta:
                error_level = ErrSeverity.LOW
            else:
                error_level = ErrSeverity.NORM

        if error_level is None:
            return

        common_msg = "Различия между оригинальным и модифицированным предложением %s для %s (различаются на %f%%)"
        self._errors.append(
            ChunkError(common_msg % (msg,
                                     chunks.mod_type_to_str(chunk.get_mod_type()),
                                     diff_perc),
                       chunk.get_chunk_id(),
                       error_level))

class PRChecker(BaseChunkSimChecker):
    """Paraphrases checker.
    """
    def __init__(self, opts, fluctuation_delta=3):
        super(PRChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.LPR and chunk.get_mod_type() != ModType.HPR:
            return
        super(PRChecker, self).__call__(chunk, src_docs)

class AddChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(AddChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.ADD:
            return
        super(AddChecker, self).__call__(chunk, src_docs)
        if len(chunk.get_orig_tokens()) >= \
           len(chunk.get_mod_tokens()):
            self._errors.append(
                ChunkError("Тип сокрытия ADD: количество слов в модифицированном предложении\
                меньше или равно количеству слов в оригинальном.",
                           chunk.get_chunk_id(),
                           ErrSeverity.HIGH))

class DelChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(DelChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.DEL:
            return
        super(DelChecker, self).__call__(chunk, src_docs)
        if len(chunk.get_orig_tokens()) <= \
           len(chunk.get_mod_tokens()):
            self._errors.append(
                ChunkError("Тип сокрытия DEL: количество слов в модифицированном предложении\
                больше или равно количеству слов в оригинальном.",
                           chunk.get_chunk_id(),
                           ErrSeverity.HIGH))

class CPYChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(CPYChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.CPY:
            return
        super(CPYChecker, self).__call__(chunk, src_docs)

class SspChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(SspChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.SSP and \
           chunk.get_mod_type() != ModType.SEP:
            return
        super(SspChecker, self).__call__(chunk, src_docs)



class CctChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(CctChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):

        if not chunk.has_mod_type(ModType.CCT):
            return

        orig_sents = chunk.get_orig_sents()
        if len(orig_sents) < 2:
            self._errors.append(ChunkError(
                "Тип заимствования CCT: оригинальный фрагмент должен содержать несколько предложений ",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))

        if chunk.get_mod_type() != ModType.CCT:
            return
        super(CctChecker, self).__call__(chunk, src_docs)

class SHFChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(SHFChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.SHF:
            return
        super(SHFChecker, self).__call__(chunk, src_docs)

class SYNChecker(BaseChunkSimChecker):
    def __init__(self, opts, fluctuation_delta=3):
        super(SYNChecker, self).__init__(opts, fluctuation_delta)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.SYN:
            return
        super(SYNChecker, self).__call__(chunk, src_docs)


class ORIGModTypeChecker(IChecher):
    def __init__(self):
        super(ORIGModTypeChecker, self).__init__()
        self._errors = []

    def get_errors(self):
        return self._errors


    def _try_find_chunk_in_src(self, chunk, src_docs):
        for src in src_docs:
            sent_holder = chunk.get_mod_sent_holder()
            sents = sent_holder.get_sents()
            found_sents = 0
            for num, sent in enumerate(sents):
                if sent_holder.get_sent_info(num).word_cnt < 6:
                    continue
                if src_docs[src].is_sent_in_doc(sent):
                    found_sents += 1
            if found_sents == len(sents):
                self._errors.append(ChunkError(
                    "Оригинальное предложение было найдено в документе '%s'" % \
                    src.encode("utf8"),
                    chunk.get_chunk_id(),
                    ErrSeverity.HIGH))
                break



    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.ORIG:
            return
        if chunk.get_orig_text():
            self._errors.append(ChunkError(
                "Поле 'оригинальное предложение' должно быть пустым, если это предложением написано вами",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))
        if not chunk.get_mod_text():
            self._errors.append(ChunkError(
                "Поле 'заимствованное предложение' должно быть заполнено, если это предложением написано вами",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))

        self._try_find_chunk_in_src(chunk, src_docs)


class OrigSentChecker(IChecher):
    def __init__(self, opts):
        self._opts = opts
        self._errors = []

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):

        if chunk.get_mod_type() == ModType.ORIG:
            return

        src_filename = chunk.get_orig_doc_filename()
        if not src_filename  in src_docs:
            #this another error, that is checked in another place
            return

        parsed_doc = src_docs[src_filename]
        not_found_cnt = 0
        sents = chunk.get_orig_sents()
        for sent in sents:
            if not parsed_doc.is_sent_in_doc(sent):
                not_found_cnt += 1


        if not_found_cnt == len(sents):
            self._errors.append(ChunkError(
                "Оригинальное предложение не было найдено в документе-источнике",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))

        elif not_found_cnt != 0:
            self._errors.append(ChunkError(
                "Некоторые предложения не были найдены в документе-источнике",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))


# sources



class SourceDocsChecker(IChecher):
    def __init__(self, opts):
        super(SourceDocsChecker, self).__init__()
        self._opts = opts
        self._used_source_docs_set = set()
        self._errors = []

        self._found_sources_docs = self._init_sources_dict()

    def _init_sources_dict(self):
        sources_dict = source_doc.find_src_paths(self._opts.sources_dir)
        logging.debug("found sources: %s", ", ".join(k.encode("utf8") for k in sources_dict))
        return sources_dict

    def _check_existance(self, orig_doc):
        filename = orig_doc
        return filename in self._found_sources_docs
        #path = fs.join(self._opts.sources_dir, orig_doc)
        #return fs.exists(path)

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):
        if not chunk.get_orig_doc():
            return

        if chunk.get_orig_doc() not in self._used_source_docs_set:
            self._used_source_docs_set.add(chunk.get_orig_doc())

            if not self._check_existance(chunk.get_orig_doc_filename()):

                logging.debug("this doc does not exist!! %s", chunk.get_orig_doc_filename())
                self._errors.append(ChunkError("Документ '%s' не существует " %
                                               chunk.get_orig_doc().encode("utf-8"),
                                               chunk.get_chunk_id(),
                                               ErrSeverity.HIGH))


class LexicalSimChecker(IChecher):
    def __init__(self, opts, fluctuation_delta = 10):
        self._opts              = opts
        self._fluctuation_delta = fluctuation_delta
        self._errors            = []

    def get_errors(self):
        return self._errors

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() == ModType.ORIG:
            return

        lex_dist = chunk.lexical_dist()
        lex_dist *= 100
        logging.debug("LexicalSimChecker:: lex_dist=%f", lex_dist)

        err_sev = None
        if lex_dist < self._opts.min_lexical_dist:
            err_sev = ErrSeverity.NORM
            if lex_dist + self._fluctuation_delta < self._opts.min_lexical_dist:
                err_sev = ErrSeverity.HIGH


        if err_sev is not None:
            common_msg = "Значительное совпадение по лексике у оригинального "\
                         "и модифицированного предложений (различаются на %f%%)"
            self._errors.append(
                ChunkError(common_msg % lex_dist,
                           chunk.get_chunk_id(),
                           err_sev))



class OriginalityChecker(IChecher):
    def __init__(self, opts):
        self._opts          = opts
        self._modified_text = []
        self._orig_text     = []


    def get_errors(self):
        orig= calc_originality("\n".join(self._modified_text),
                               "\n".join(self._orig_text))

        if orig < self._opts.min_originality:
            return [
                Error("Оригинальность текста слишком низкая: %.2f%%."
                      " Необходимо увеличить оригинальность до %.2f%%!" % (
                          orig * 100.0,
                          self._opts.min_originality * 100.0),
                      ErrSeverity.HIGH)
            ]
        else:
            return []

    def __call__(self, chunk, src_docs):
        self._modified_text.append(chunk.get_mod_text())
        self._orig_text.append(chunk.get_orig_text())


class SentCorrectnessChecker(IChecher):
    def __init__(self, mods = None):
        super(SentCorrectnessChecker, self).__init__()
        self._errors = []
        self._mods = mods

    def get_errors(self):
        return self._errors

    def _check_term_in_the_end(self, chunk):
        if self._mods and "term_in_the_end" not in self._mods:
            return
        text = chunk.get_mod_sents()[-1]

        if text[-1] not in segmenter.SENTENCE_TERMINALS:
            self._errors.append(ChunkError(
                "Предложение должно заканчиваться точкой (или !?)!",
                chunk.get_chunk_id(),
                ErrSeverity.NORM))

    def _check_title_case(self, chunk):
        if self._mods and "title_case" not in self._mods:
            return

        first_token = chunk.get_mod_sents()[0].split(None, 1)[0]

        #allow up to 2 punctuation characters before upper letter or digit.
        m = regex.search(ur"^\p{P}{0,2}(\p{Lu}|\d)", first_token)
        if m is None:
            self._errors.append(ChunkError(
                "Предложение должно начинаться с заглавной буквы!",
                chunk.get_chunk_id(),
                ErrSeverity.NORM))

    def __call__(self, chunk, _):
        self._check_term_in_the_end(chunk)
        self._check_title_case(chunk)
