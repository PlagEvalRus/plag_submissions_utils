#!/usr/bin/env python
# coding: utf-8

import logging
from collections import Counter
from collections import defaultdict
import itertools

from segtok import segmenter
import regex
import re
import hunspell
import langdetect

from . import text_proc
from . import source_doc
from . import chunks
from . import homoglyphs
from .chunks import ModType
from .errors import ErrSeverity
from .errors import ChunkError
from .errors import Error
from .simple_detector import calc_originality


class IChecher(object):
    def get_errors(self):
        raise NotImplementedError("Should implement this!")

    def __call__(self, chunk, src_docs):
        raise NotImplementedError("Should implement this!")

class IFixableChecker(IChecher):
    def fix_all(self, all_chunks):
        raise NotImplementedError("Should implement this!")


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


class CyrillicAlphabetChecker(IFixableChecker):
    def __init__(self, opts):
        super(CyrillicAlphabetChecker, self).__init__()
        self._errors = []

    def get_errors(self):
        return self._errors

    def _find_homoglyphs(self, chunk):
        """Example:
        _find_homoglyphs(u"искуᏟꓚCСTвенный")

        returns:
        [{'alias': u'CHEROKEE',
        'character': u'\u13df',
        'homoglyphs': {'a': u'CYRILLIC', 'c': u'\u0421'}},
        {'alias': u'LISU',
        'character': u'\ua4da',
        'homoglyphs': {'a': u'CYRILLIC', 'c': u'\u0421'}},
        {'alias': u'LATIN',
        'character': u'C',
        'homoglyphs': {'a': u'CYRILLIC', 'c': u'\u0421'}},
        {'alias': u'LATIN',
        'character': u'T',
        'homoglyphs': {'a': u'CYRILLIC', 'c': u'\u0422'}}]
        """

        found = []
        for sent_num, s in enumerate(chunk.get_mod_sents()):
            for m in re.finditer(ur"[\w']+", s, re.UNICODE):
                token = m.group()
                #do not check words in latin or other alphabet
                if not re.search(u'[а-яА-Я]', token, re.UNICODE):
                    continue
                confusable_chars = homoglyphs.find_homoglyphs(token, ['CYRILLIC'])
                if confusable_chars:
                    for char_info in confusable_chars:

                        if ord(char_info['character']) >=48 and \
                           ord(char_info['character']) <= 57:
                            #skip numbers
                            continue
                        char_info['word'] = token
                        char_info['sent_num'] = sent_num
                        char_info['pos'] = m.start() + char_info['pos']
                        found.append(char_info)

        return found


    def __call__(self, chunk, src_docs):
        reports = []
        found = self._find_homoglyphs(chunk)

        for char_info in found:
            reports.append('В слове "{}" заменена буква "{}" на "{}" ({}).'.format(
                char_info['word'].encode('utf-8'),
                char_info['homoglyphs']['c'].encode('utf8'),
                char_info['character'].encode('utf8'),
                char_info['alias'].encode('utf8')))

        if reports:
            self._errors.append(
                ChunkError(
                    "Модифицированное предложение содержит замены отдельных букв! {}"
                    .format(';'.join(reports)),
                    chunk.get_chunk_id(),
                    ErrSeverity.HIGH))


    def fix(self, chunk):
        found = self._find_homoglyphs(chunk)
        if not found:
            return

        new_sents = []
        char_info_num = 0
        for sent_num, sent in enumerate(chunk.get_mod_sents()):
            char_info = found[char_info_num]
            new_sent = []
            for sent_pos, char in enumerate(sent):
                if char_info['sent_num'] == sent_num and char_info['pos'] == sent_pos:
                    logging.info("Replace '%s' (%s) with '%s'", char, char_info['alias'],
                                  char_info['homoglyphs']['c'])
                    new_sent.append(char_info['homoglyphs']['c'])
                    if char_info_num + 1 < len(found):
                        char_info_num += 1
                        char_info = found[char_info_num]
                else:
                    new_sent.append(char)
            new_sents.append(u''.join(new_sent))

        chunk.get_mod_sents()[:] = new_sents

    def fix_all(self, all_chunks):
        for chunk in all_chunks:
            self.fix(chunk)


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


    def _should_run(self, chunk):
        return chunk.get_mod_type() == ModType.ORIG


    def __call__(self, chunk, src_docs):
        if not self._should_run(chunk):
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
                "Исходное предложение не было найдено в документе-источнике",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))

        elif not_found_cnt != 0:
            self._errors.append(ChunkError(
                "Некоторые предложения не были найдены в документе-источнике",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))


# sources



class SourceDocsChecker(IChecher):
    def __init__(self, opts, sources_dir):
        super(SourceDocsChecker, self).__init__()
        self._opts = opts
        self._used_source_docs_set = set()
        self._errors = []

        self._found_sources_docs = self._init_sources_dict(sources_dir)

    def _init_sources_dict(self, sources_dir):
        sources_dict = source_doc.find_src_paths(sources_dir)
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


class SentCorrectnessChecker(IFixableChecker):
    def __init__(self, mods = None):
        super(SentCorrectnessChecker, self).__init__()
        self._errors = []
        self._mods = mods

    def get_errors(self):
        return self._errors

    def _find_sents_wo_term_in_the_end(self, chunk):
        sents_with_errors = []

        if self._mods and "term_in_the_end" not in self._mods:
            return sents_with_errors

        for num, s in enumerate(chunk.get_mod_sents()):
            if s[-1] not in segmenter.SENTENCE_TERMINALS:
                sents_with_errors.append(num)

        return sents_with_errors

    def _find_sents_wo_title_case(self, chunk):
        sents_with_errors = []

        if self._mods and "title_case" not in self._mods:
            return sents_with_errors

        for num, s in enumerate(chunk.get_mod_sents()):
            first_token = s.split(None, 1)[0]

            #allow up to 2 punctuation characters before upper letter or digit.
            m = regex.search(ur"^\p{P}{0,2}(\p{Lu}|\d)", first_token)
            if m is None:
                sents_with_errors.append(num)

        return sents_with_errors


    def __call__(self, chunk, _):
        if self._find_sents_wo_term_in_the_end(chunk):
            self._errors.append(ChunkError(
                "Предложение должно заканчиваться точкой (или !?)!",
                chunk.get_chunk_id(),
                ErrSeverity.NORM))

        if self._find_sents_wo_title_case(chunk):
            self._errors.append(ChunkError(
                "Предложение должно начинаться с заглавной буквы!",
                chunk.get_chunk_id(),
                ErrSeverity.NORM))


    def fix(self, chunk):
        sents = chunk.get_mod_sents()

        sents_wo_term = self._find_sents_wo_term_in_the_end(chunk)

        for snum in sents_wo_term:
            sents[snum] = sents[snum] + '.'

        sents_wo_title_case = self._find_sents_wo_title_case(chunk)

        for snum in sents_wo_title_case:
            if len(sents[snum]) < 2:
                continue
            if sents[snum][0] in ['.', ',', '!', '?']:
                temp_sent = sents[snum][1:].strip()
            else:
                temp_sent = sents[snum]

            sents[snum] = temp_sent[0].upper() + temp_sent[1:]

        return len(sents_wo_term), len(sents_wo_title_case)

    def fix_all(self, all_chunks):
        sents_wo_term_cnt = 0
        sents_wo_title_case_cnt = 0
        for chunk in all_chunks:
            t, c = self.fix(chunk)
            sents_wo_term_cnt += t
            sents_wo_title_case_cnt += c
        logging.info("Fixed %d sents with no term in the end", sents_wo_term_cnt)
        logging.info("Fixed %d sents with title case", sents_wo_title_case_cnt)

class SpellChecker(IFixableChecker):
    DICT_PREFIX = '/usr/share/hunspell'

    def __init__(self, high_rate = 0.1, norm_rate = 0.01,
                 lang_hint = 'ru', whitelist = None):
        super(SpellChecker, self).__init__()
        self._last_lang                = lang_hint
        self._errors                   = []
        self._dicts                    = {}
        self._white_list = frozenset(whitelist) if whitelist else frozenset()


        self._tokens_cnt               = 0
        self._typo_max_tf              = 8
        self._typo_sents_dict         = defaultdict(lambda : [])
        self._all_sents                = 0

        #error rates
        self._high_rate                = high_rate
        self._norm_rate                = norm_rate

        self._counter                  = Counter()



    def _drop_most_common(self):
        """ "typos" that are encountered more than typo_max_tf times are not typos...
        """
        for typo in self._counter.keys():
            if self._counter[typo] >= self._typo_max_tf:
                del self._typo_sents_dict[typo]
                del self._counter[typo]

    def _get_stat(self):
        sents_set =  set(i['chunk_id']
                         for i in itertools.chain(*self._typo_sents_dict.itervalues()))
        wrong_spelled_tokens = len(self._counter)
        return sents_set, wrong_spelled_tokens

    def _make_err_msg(self):
        typo_with_sents = self._typo_sents_dict.items()
        typo_with_sents.sort(key= lambda p : p[1][0])
        typo_with_sents_str = [u"%s: № %s" % (t, u", ".join(str(i['chunk_id']) for i in infos))
                               for t, infos in typo_with_sents]
        err_msg = "Слишком много опечаток в заимствованном тексте! " \
                  "Проверьте следующие предложения:\n"

        return err_msg, typo_with_sents_str


    def get_errors(self):
        if self._tokens_cnt == 0:
            return self._errors

        self._drop_most_common()
        sents_set, wrong_spelled_tokens = self._get_stat()

        logging.debug("SpellChecker: typos cnt: %s, all tokens: %s",
                      wrong_spelled_tokens,
                      self._tokens_cnt)


        err_msg, extra = self._make_err_msg()

        typos_rate = wrong_spelled_tokens / float(self._tokens_cnt)
        sents_with_typos_rate = float(len(sents_set))/ self._all_sents
        if sents_with_typos_rate > 0.3 or typos_rate > self._high_rate:
            self._errors.append(
                Error(err_msg, ErrSeverity.HIGH, extra))
        elif typos_rate > self._norm_rate:
            self._errors.append(Error(err_msg, ErrSeverity.NORM, extra))

        return self._errors


    def _detect_lang(self, chunk):
        lang = langdetect.detect(chunk.get_mod_text())
        if lang not in ['ru', 'en']:
            logging.debug("Failed to detect lang; Fallback to last detected: %s",
                          self._last_lang)
            return self._last_lang

        self._last_lang = lang
        return lang

    def _get_dict(self, chunk):
        lang = self._detect_lang(chunk)

        if lang in self._dicts:
            return self._dicts[lang]

        if lang == 'ru':
            dict_name = 'ru_RU'
        else:
            dict_name = 'en_US'

        self._dicts[lang] = hunspell.HunSpell(
            '%s/%s.dic' % (self.DICT_PREFIX, dict_name),
            '%s/%s.aff' % (self.DICT_PREFIX, dict_name))

        return self._dicts[lang]



    def _find_typos(self, chunk):
        if chunk.get_mod_type() == ModType.CPY:
            return

        self._all_sents += 1
        spell_dict = self._get_dict(chunk)
        if spell_dict is None:
            return

        tokens = [t for s in chunk.get_mod_sents()
                  for t in text_proc.tok_sent(s, make_lower = False)]

        for token in tokens:
            #yeah we're gonna skip the first word in the sentence.
            #but we also skip all named entities (poor man's named entity recognition)
            if token[0].isupper():
                continue
            if len(token) <= 2:
                continue


            self._tokens_cnt += 1

            if token.lower() in self._white_list:
                continue

            enc_token = token.encode(spell_dict.get_dic_encoding(), 'replace')
            if not spell_dict.spell(enc_token):
                suggestions = spell_dict.suggest(enc_token)
                if not suggestions:
                    continue

                suggestions = [s.decode(spell_dict.get_dic_encoding()) for s in suggestions]
                token_key = token.lower()
                self._counter[token_key] +=1
                self._typo_sents_dict[token_key].append({'chunk_id': chunk.get_chunk_id(),
                                                         'typo': token,
                                                         'suggest': suggestions})

    def __call__(self, chunk, _):
        self._find_typos(chunk)


    def fix_all(self, all_chunks):
        for chunk in all_chunks:
            self._find_typos(chunk)

        self._drop_most_common()

        typos_per_chunk_dict = defaultdict(lambda:[])
        for typo_occs in self._typo_sents_dict.itervalues():
            for i in typo_occs:
                typos_per_chunk_dict[i['chunk_id']].append(i)

        for chunk in all_chunks:
            if chunk.get_chunk_id() not in typos_per_chunk_dict:
                continue

            new_sents = []
            for sent in chunk.get_mod_sents():
                for typo_info in typos_per_chunk_dict[chunk.get_chunk_id()]:
                    sent = sent.replace(typo_info['typo'], typo_info['suggest'][0])
                    logging.info("Replaced %s with %s", typo_info['typo'], typo_info['suggest'][0])
                new_sents.append(sent)

            chunk.get_mod_sents()[:] = new_sents
