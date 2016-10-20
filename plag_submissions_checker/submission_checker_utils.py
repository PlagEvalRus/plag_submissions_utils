#!/usr/bin/env python
# -*- coding:utf-8 -*-

from collections import defaultdict
import logging

import difflib
import os.path as fs
import os
import pipes
import re
import subprocess


import distance
import segtok.segmenter as seg
import segtok.tokenizer as tok
import pyunpack as arc
import regex
import xlrd


# Begin of  Errors
class ErrSeverity(object):
    LOW = 0
    NORM = 1
    HIGH = 2

class Error(object):
    def __init__(self, msg, sev = ErrSeverity.NORM):
        self.msg = msg
        self.sev = sev
    def __str__(self):
        return "!" * self.sev + self.msg

class ChunkError(Error):
    def __init__(self, msg, chunk_num, sev = ErrSeverity.NORM):
        super(ChunkError, self).__init__(msg, sev)
        self.chunk_num = chunk_num
    def __str__(self):
        pref = "!" * self.sev
        return  "%s Предложение #%d: %s" %(pref, self.chunk_num, self.msg)

# End of Errors


# Begin of Chunks

class ModType(object):
    UNK  = 0
    CPY  = 1
    LPR  = 2
    HPR  = 3
    ORIG = 4
    DEL  = 5
    ADD  = 6
    CCT  = 7
    SSP  = 8

    @classmethod
    def get_all_mods_type(cls):
        return range(0,9)

def mod_type_to_str(mod_type):
    mod_type_dict = {
        0 : "UNK",
        1 : "CPY",
        2 : "LPR",
        3 : "HPR",
        4 : "ORIG",
        5 : "DEL",
        6 : "ADD",
        7 : "CCT",
        8 : "SSP"
    }
    return mod_type_dict.get(mod_type, "unk")

def _create_mod_type(mod_str):
    mls = mod_str.strip().lower()
    if not mls:
        return ModType.ORIG
    elif mls == "cpy":
        return ModType.CPY
    elif mls == "lpr":
        return ModType.LPR
    elif mls == "hpr":
        return ModType.HPR
    elif mls == "del":
        return ModType.DEL
    elif mls == "add":
        return ModType.ADD
    elif mls == "ssp":
        return ModType.SSP
    elif mls == "cct":
        return ModType.CCT
    else:
        return ModType.UNK

class SentInfo(object):
    """Documentation for SentInfo

    """
    def __init__(self, word_cnt):
        super(SentInfo, self).__init__()
        self.word_cnt = word_cnt


def create_sent_info(sent):
    tokens = tok_sent(sent)
    return SentInfo(len(tokens))

class SentsHolder(object):
    """Documentation for SentsHolder

    """
    def __init__(self, text):
        super(SentsHolder, self).__init__()
        self._text       = text
        self._sents      = seg_text_as_list(text)
        self._sent_tokens = [tok_sent(s) for s in self._sents]
        self._sent_infos = [SentInfo(len(t)) for t in self._sent_tokens]

    def get_avg_words_cnt(self):
        words_cnt = sum(si.word_cnt for si in self._sent_infos)
        return float(words_cnt)/ len(self._sent_infos)

    def get_sents(self):
        return self._sents

    def get_text(self):
        return self._text

    def get_all_tokens(self):
        all_tokens = []
        for t in self._sent_tokens:
            all_tokens.extend(t)
        return all_tokens

    def get_tokens_list(self):
        return self._sent_tokens



class Chunk(object):
    def __init__(self, orig_text, mod_text,
                 mod_type_str, orig_doc, chunk_num):
        self._chunk_num           = chunk_num
        self._original_sents      = SentsHolder(orig_text)
        self._modified_sents      = SentsHolder(mod_text)
        self._mod_type            = _create_mod_type(mod_type_str)
        self._orig_doc            = orig_doc


    def get_chunk_id(self):
        return self._chunk_num

    def get_mod_type(self):
        return self._mod_type

    def get_orig_doc(self):
        return self._orig_doc

    def get_orig_doc_filename(self):
        return _get_src_filename(self._orig_doc)

    def get_avg_original_words_cnt(self):
        return self._original_sents.get_avg_words_cnt()

    def get_avg_modified_words_cnt(self):
        return self._modified_sents.get_avg_words_cnt()

    def measure_dist(self):
        return distance.nlevenshtein(self._original_sents.get_all_tokens(),
                                     self._modified_sents.get_all_tokens())

    def get_orig_sents(self):
        return self._original_sents.get_sents()

    def get_modified_sents(self):
        return self._modified_sents.get_sents()

    def get_orig_tokens(self):
        return self._original_sents.get_all_tokens()

    def get_orig_tokens_list(self):
        return self._original_sents.get_tokens_list()

    def get_mod_tokens(self):
        return self._modified_sents.get_all_tokens()

    def get_orig_text(self):
        return self._original_sents.get_text()

    def get_mod_text(self):
        return self._modified_sents.get_text()

    def __str__(self):
        chunk_str = "%d (%s): %s, %s" %(
            self._chunk_num,
            mod_type_to_str(self._mod_type),
            u" ".join(self._modified_sents.get_sents()).encode("utf8"),
            u"|".join(self._modified_sents.get_all_tokens()).encode("utf8"))
        return chunk_str


#End of Chunks

#Begin of Stat

class SubmissionStat(object):
    """Documentation for SubmissionStat

    """
    def __init__(self, chunks_cnt,
                 orig_sent_lengths = None,
                 mod_sent_lengths = None,
                 mod_type_freqs = None,
                 docs_freqs = None):
        super(SubmissionStat, self).__init__()
        self.chunks_cnt        = chunks_cnt
        self.orig_sent_lengths = orig_sent_lengths if orig_sent_lengths is not None else []
        self.mod_sent_lengths  = mod_sent_lengths if mod_sent_lengths is not None else []
        self.mod_type_freqs    = mod_type_freqs if mod_type_freqs is not None else defaultdict(lambda : 0)
        self.docs_freqs        = docs_freqs if docs_freqs is not None else defaultdict(lambda : 0)

    def _defdict_to_str(self, defdict, val_trans = lambda v: v, key_trans = lambda k : k):
        return "\n".join("%s : %s" % (key_trans(k), val_trans(v)) for k, v in defdict.iteritems())

    def __str__(self):
        len_parts = []
        for num in range(len(self.orig_sent_lengths)):
            len_parts.append("%d: %f, %f" %(self.orig_sent_lengths[num][0],
                                            self.mod_sent_lengths[num][1],
                                            self.orig_sent_lengths[num][1]))


        return """Total chunks cnt: %d
Sent lengths: %s
Mod type frequencies: %s
Docs frequencies: %s""" %(self.chunks_cnt,
                          "\n".join(len_parts),
                          self._defdict_to_str(self.mod_type_freqs),
                          self._defdict_to_str(self.docs_freqs, key_trans = lambda k: k.encode("utf8")))



class StatCollector(object):
    def __init__(self):
        pass

    def __call__(self, chunks):
        stat = SubmissionStat(len(chunks))
        for chunk in chunks:
            stat.orig_sent_lengths.append((chunk.get_chunk_id(),
                                           chunk.get_avg_original_words_cnt()))

            stat.mod_sent_lengths.append((chunk.get_chunk_id(),
                                          chunk.get_avg_modified_words_cnt()))

            stat.mod_type_freqs[chunk.get_mod_type()] += 1
            if chunk.get_mod_type() != ModType.ORIG:
                stat.docs_freqs[chunk.get_orig_doc()] += 1

        return stat

#End of Stat



# Begin of checkers

class IChecher(object):
    def get_errors(self):
        raise NotImplementedError("should implement this!")

    def __call__(self, chunk, src_docs):
        raise NotImplementedError("should implement this!")


class BaseChunkSimChecker(IChecher):
    def __init__(self, opts, low_level_thresh = 10):
        self._opts = opts
        self._diff_perc_dict = opts.diff_perc
        self._low_level_thresh = low_level_thresh
        self._errors = []

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
        if etal_diff_perc_tuple[0] > diff_perc:
            msg = "малы"
            if etal_diff_perc_tuple[0] <= \
               diff_perc + self._low_level_thresh:
                error_level = ErrSeverity.LOW
            elif diff_perc < 3:
                error_level = ErrSeverity.HIGH
            else:
                error_level = ErrSeverity.NORM
        elif etal_diff_perc_tuple[1] < diff_perc:
            msg = "слишком велики"
            if etal_diff_perc_tuple[1] >= \
               diff_perc - self._low_level_thresh:
                error_level = ErrSeverity.LOW
            else:
                error_level = ErrSeverity.NORM

        if error_level is None:
            return

        common_msg = "Различия между оригинальным и модифицированным предложением %s для %s (различаются на %f%%)"
        self._errors.append(
            ChunkError(common_msg % (msg,
                                     mod_type_to_str(chunk.get_mod_type()),
                                     diff_perc),
                       chunk.get_chunk_id(),
                       error_level))

class PRChecker(BaseChunkSimChecker):
    def __init__(self, opts):
        super(PRChecker, self).__init__(opts)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.LPR and chunk.get_mod_type() != ModType.HPR:
            return
        super(PRChecker, self).__call__(chunk, src_docs)

class AddChecker(BaseChunkSimChecker):
    def __init__(self, opts):
        super(AddChecker, self).__init__(opts)

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
    def __init__(self, opts):
        super(DelChecker, self).__init__(opts)

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
    def __init__(self, opts):
        super(CPYChecker, self).__init__(opts)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.CPY:
            return
        super(CPYChecker, self).__call__(chunk, src_docs)

class SspChecker(BaseChunkSimChecker):
    def __init__(self, opts):
        super(SspChecker, self).__init__(opts)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.SSP:
            return
        super(SspChecker, self).__call__(chunk, src_docs)

class CctChecker(BaseChunkSimChecker):
    def __init__(self, opts):
        super(CctChecker, self).__init__(opts)

    def __call__(self, chunk, src_docs):
        if chunk.get_mod_type() != ModType.CCT:
            return
        super(CctChecker, self).__call__(chunk, src_docs)
        orig_sents = chunk.get_orig_sents()
        if len(orig_sents) < 2:
            self._errors.append(ChunkError(
                "Тип заимствования CCT: оригинальный фрагмент должен содержать несколько предложений ",
                chunk.get_chunk_id(),
                ErrSeverity.HIGH))

class ORIGModTypeChecker(IChecher):
    def __init__(self):
        super(ORIGModTypeChecker, self).__init__()
        self._errors = []

    def get_errors(self):
        return self._errors

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

        if chunk.get_mod_type() == ModType.CCT:
            orig_tokens_list = chunk.get_orig_tokens_list()
        else:
            orig_tokens_list = [chunk.get_orig_tokens()]

        parsed_doc = src_docs[src_filename]
        not_found_cnt = 0
        for tokens in orig_tokens_list:
            if not parsed_doc.is_sent_in_doc(tokens):
                not_found_cnt += 1


        if not_found_cnt == len(orig_tokens_list):
            self._errors.append(ChunkError("Оригинальное предложение не было найдено в документе-источнике",
                                           chunk.get_chunk_id(),
                                           ErrSeverity.HIGH))

        elif not_found_cnt != 0:
            self._errors.append(ChunkError("Некоторые предложения не были найдены в документе-источнике", chunk.get_chunk_id()))


# sources
def _get_src_filename(path):
    if isinstance(path, unicode):
        uni_path = path
    elif isinstance(path, str):
        uni_path = path.decode("utf-8")
    else:
        uni_path = unicode(str(path), encoding="utf8")
    return fs.splitext(fs.basename(uni_path))[0]


class SourceDocsChecker(IChecher):
    def __init__(self, opts):
        super(SourceDocsChecker, self).__init__()
        self._opts = opts
        self._used_source_docs_set = set()
        self._errors = []

        self._found_sources_docs = self._init_sources_dict()

    def _init_sources_dict(self):
        sources_dict = {}
        entries = os.listdir(self._opts.sources_dir)
        for entry in entries:
            doc_path = fs.join(self._opts.sources_dir, entry)
            if not fs.isfile(doc_path):
                continue
            filename = _get_src_filename(entry)
            if filename in sources_dict:
                self._errors.append(Error("Документы-источники дублируются", ErrSeverity.HIGH))
            else:
                sources_dict[filename] = doc_path
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

# end of checkers



# begin of metrics
class ViolationLevel(object):
    OK = 0
    MEDIUM = 1
    HIGH = 2

class IMetric(object):
    """Documentation for IMetric

    """

    def get_value(self):
        raise NotImplementedError("should implement this!")

    def get_violation_level(self):
        raise NotImplementedError("should implement this!")

    def __call__(self, stat, chunks):
        raise NotImplementedError("should implement this!")

class SrcDocsCountMetric(IMetric):
    def __init__(self, min_docs_cnt, min_sent_per_src):
        self._min_docs_cnt     = min_docs_cnt
        self._min_sent_per_src = min_sent_per_src
        self._docs_cnt         = 0

    def get_value(self):
        return self._docs_cnt

    def get_violation_level(self):
        if self._min_docs_cnt > self._docs_cnt:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        self._docs_cnt = sum(1 for k in stat.docs_freqs if stat.docs_freqs[k] >= self._min_sent_per_src)

    def __str__(self):
        return "Количество документов-источников, из которых взято более %d предложений : %d" % (self._min_sent_per_src, self._docs_cnt)

class DocSizeMetric(IMetric):
    def __init__(self, min_real_sent_cnt, min_sent_size,
                 medium_thresh = 10):
        self._min_real_sent_cnt = min_real_sent_cnt
        self._min_sent_size     = min_sent_size
        self._medium_thresh     = medium_thresh
        self._real_sent_cnt     = 0

    def get_value(self):
        return self._real_sent_cnt

    def get_violation_level(self):
        if self._min_real_sent_cnt > self._real_sent_cnt:
            if self._min_real_sent_cnt <= \
               self._real_sent_cnt + self._medium_thresh:
                return ViolationLevel.MEDIUM
            else:
                return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        self._real_sent_cnt = sum(1 for t in stat.mod_sent_lengths if t[1] > self._min_sent_size)

    def __str__(self):
        return "Количество предложений, размер которых превышает %d слов: %d" % (
            self._min_sent_size, self._real_sent_cnt)


class ModTypeRatioMetric(IMetric):
    def __init__(self, mod_type, ratio_interval,
                 medium_thresh = 5):
        self._mod_type      = mod_type
        self._ratio_interval = ratio_interval
        self._medium_thresh = medium_thresh
        self._mod_type_ratio = 0

    def get_value(self):
        return self._mod_type_ratio

    def strict_mod(self):
        if self._ratio_interval[0] > self._mod_type_ratio:
                return ViolationLevel.HIGH
        elif self._ratio_interval[1] < self._mod_type_ratio:
            return ViolationLevel.HIGH
        else:
            return ViolationLevel.OK

    def get_violation_level(self):
        if self._mod_type_ratio != 0 and \
           self._mod_type == ModType.UNK:
            return ViolationLevel.HIGH

        if self._mod_type_ratio == 0 and \
           self._mod_type != ModType.UNK and \
           self._mod_type != ModType.CPY and \
           self._mod_type != ModType.ORIG:
            return ViolationLevel.HIGH

        if self._mod_type == ModType.CPY:
            return self.strict_mod()

        # all other modes are
        #non strict (there may be some fluctuations from required interval)
        logging.debug("mod type %d, %s %f", self._mod_type,
                      self._ratio_interval, self._mod_type_ratio)
        if self._ratio_interval[0] > self._mod_type_ratio:
            if self._ratio_interval[0] <= \
               self._mod_type_ratio + self._medium_thresh:
                return ViolationLevel.MEDIUM
            else:
                return ViolationLevel.HIGH
        elif self._ratio_interval[1] < self._mod_type_ratio:
            return ViolationLevel.MEDIUM
        else:
            return ViolationLevel.OK

    def __call__(self, stat, chunks):
        mod_type_cnt = stat.mod_type_freqs[self._mod_type]
        self._mod_type_ratio = float(mod_type_cnt) / stat.chunks_cnt
        self._mod_type_ratio *= 100
        self._mod_type_ratio = round(self._mod_type_ratio, 1)

    def __str__(self):
        common = "%.1f%% предложений имеют тип: %s" % (
            self.get_value(), mod_type_to_str(self._mod_type))
        if self._mod_type == ModType.UNK:
            return common + " (UNK означает неизвестный тип сокрытия. "\
                "Скорее всего в названии некоторых типов сокрытий опечатка.)"
        else:
            return common


# end of metrics

class PocesssorOpts(object):
    def __init__(self, sources_dir, inp_file):
        self.sources_dir       = sources_dir
        self.inp_file          = inp_file
        self.min_src_docs      = 5
        self.min_sent_per_src  = 4
        self.min_sent_size     = 5
        self.min_real_sent_cnt = 150
        self.mod_type_ratios   = {
            0 : (0,0),
            1 : (0, 10),
            2 : (10, 30),
            3 : (10, 20),
            4 : (0, 30),
            5 : (20, 30),
            6 : (15, 25),
            7 : (5, 15),
            8 : (5, 15)
        }
        #допустимый процент изменений для каждого типа сокрытия
        self.diff_perc         = {
            1 : (0, 0),
            2 : (10, 75),
            3 : (30, 100),
            4 : (100, 100),
            5 : (20, 70),
            6 : (20, 70),
            7 : (0, 75),
            8 : (0, 80)
        }

        self.errors_level = ErrSeverity.NORM

class Processor(object):
    def __init__(self, opts, checkers,
                 metrics,
                 stat_collecter = None):
        self._opts           = opts

        self._checkers       = checkers
        self._metrics        = metrics
        self._stat_collecter = stat_collecter if stat_collecter is not None else StatCollector()


    def _try_create_chunk(self, row_vals, sent_num, vals_offs):
        def check_str_cell(cell_val):
            if not isinstance(cell_val, (str, unicode)):
                raise RuntimeError("Sent # %d; Wrong value of the cell: %s"
                                   % (sent_num, str(cell_val)))
            return cell_val

        return Chunk(mod_text = row_vals[vals_offs + 0],
                     orig_text = check_str_cell(row_vals[vals_offs + 1]),
                     orig_doc = row_vals[vals_offs + 2],
                     mod_type_str = check_str_cell(row_vals[vals_offs + 3]),
                     chunk_num = sent_num)

    def _process_chunk(self, chunk, src_docs):

        for checker in self._checkers:
            try:
                checker(chunk, src_docs)
            except Exception as e:
                logging.exception("during proc %d: ", chunk.get_chunk_id())

    #TODO: move to distinct function,
    # unite with _init_sources_dict
    def _load_sources_docs(self):
        sources_dict = {}
        entries = os.listdir(self._opts.sources_dir)
        for entry in entries:
            try:
                doc_path = fs.join(self._opts.sources_dir, entry)
                doc_path = fs.abspath(doc_path)
                if not fs.isfile(doc_path):
                    continue
                filename = _get_src_filename(entry)
                if filename in sources_dict:
                    logging.warning("source document with such filename %s already exists", filename)
                else:
                    sources_dict[filename] = SourceDoc(doc_path)
            except Exception as e:
                logging.warning("failed to parse %s: %s", doc_path, e)

        return sources_dict

    def _try_to_extract_sent_num(self, rownum, is_col_num_cell_found,
                                 col_num_cell_content):
        #+1 for header row
        dummy_sent_num = rownum + 1
        if is_col_num_cell_found:
            #there is a column with numbers
            #no one follows the guide
            #There maybe be 1. 2.; 1!, 2!...
            if isinstance(col_num_cell_content, (str, unicode)):
                if not col_num_cell_content:
                    #cell is empty, may be they forgot to continue numeration...
                    return dummy_sent_num
                m = re.search(r"(\d+)", col_num_cell_content)
                if m is None:
                    raise RuntimeError("Failed to extract sent number from 0 column")
                return int(m.group(1))

            elif isinstance(col_num_cell_content, (int, float)):
                return int(col_num_cell_content)

        else:
            return dummy_sent_num


    def _create_chunks(self):
        errors = []
        book = xlrd.open_workbook(self._opts.inp_file)
        sheet = book.sheet_by_index(0)
        if sheet.nrows <= 2:
            errors.append(Error("Sheet contains 2 or less rows!!",
                                ErrSeverity.HIGH))
            return [], errors

        if sheet.row_values(0)[0].lower().find(u"номер") == -1:
            #no one follows the guide
            #there may be no header or it may be # or № or 'Меня зовут Вася'
            try:
                int(sheet.row_values(1)[0])
                #hmm this column contains number it must be a 'Номер' column
                main_content_offs = 1
            except ValueError:
                #it is not number
                main_content_offs = 0
        else:
            main_content_offs = 1

        chunks = []
        for rownum in range(1, sheet.nrows):
            row_vals = sheet.row_values(rownum)
            try:
                sent_num = self._try_to_extract_sent_num(rownum,
                                                         main_content_offs == 1,
                                                         row_vals[0])
                chunk = self._try_create_chunk(
                    row_vals,
                    sent_num,
                    main_content_offs)
                logging.debug("parsed chunk: %s", chunk)
                chunks.append(chunk)
            except Exception as e:
                logging.exception("failed to create chunk: %s ", str(e))
                errors.append(Error("Не удалось проанализировать ряд с номером %d: %s" %
                                    (rownum, str(e)),
                                    ErrSeverity.HIGH))


        return chunks, errors

    def check(self):

        chunks, errors = self._create_chunks()
        stat = self._stat_collecter(chunks)
        logging.debug("collected stat: %s", stat)
        if stat.chunks_cnt == 0:
            return [Error("Не удалось проанализировать ни один фрагмент",
                          ErrSeverity.HIGH)], stat


        for metric in self._metrics:
            metric(stat, chunks)

        src_docs = self._load_sources_docs()
        for chunk in chunks:
            self._process_chunk(chunk, src_docs)

        for checker in self._checkers:
            errors.extend(e for e in checker.get_errors())

        errors = [e for e in errors if e.sev >= self._opts.errors_level]
        errors.sort(key=lambda e : e.sev, reverse = True)

        return errors, stat


# begin doc operations


def ispunct(st):
    # return all(ch in string.punctuation for ch in st)
    return not st.isalnum()

def seg_text_as_list(text):
    # convert from generator to list
    return [s for s in seg_text(text)]

def seg_text(text):
    #clean all shitty \r\n and so on...
    text = u" ".join(text.split())
    #some documents contain "заповеди Пифагора.Нравственные"
    # or "психотерапии . Они"
    #regex supports unicode uppercase letters - \p{Lu}
    text = regex.sub(ur"(\p{Ll})\s?\.\s?(\p{Lu})", ur"\1. \2", text)
    return seg.split_single(text)

def tok_sent(sent):
    tokens = tok.symbol_tokenizer(sent)
    return [s.lower() for s in tokens if not ispunct(s)]

def convert_doc(doc_path):
    #tika's pdf converter is not very good
    if doc_path.endswith("pdf"):
        cmd = "pdftotext %s -" % pipes.quote(doc_path)
    else:
        cmd = "/compiled/bin/tika --text %s" % pipes.quote(doc_path)
    # textract html converter is not very good
    # cmd = "textract %s" % pipes.quote(doc_path)
    text = subprocess.check_output(cmd, shell=True)
    return text.decode("utf8")

def strip_text(sent):
    return u" ".join(tok_sent(sent))

def _gen_mega_regexp(text):
    return ur"-?\s*".join(ch for ch in text if ch.isalnum())

class SourceDoc(object):
    def __init__(self, doc_path, max_length_delta = 0,
                 max_offs_delta = 22):
        logging.debug("trying to parse %s", doc_path)
        text                   = convert_doc(doc_path)
        self._doc_tokens       = tok_sent(text)
        self._text             = u" ".join(self._doc_tokens)
        logging.debug("stripped source doc: %s", self._text)

        self._max_length_delta = max_length_delta
        self._max_offs_delta   = max_offs_delta

    def _try_sequence_matcher(self, tokens):
        matcher = difflib.SequenceMatcher(a = self._doc_tokens,
                                          b = tokens,
                                          autojunk = False)
        #find seed
        longest_match = matcher.find_longest_match(0, len(self._doc_tokens),
                                                   0, len(tokens))

        left_a_pos = longest_match.a - (longest_match.b - 1) - self._max_offs_delta
        left_a_pos = max(0, left_a_pos)
        right_a_pos = longest_match.a + longest_match.size + (len(tokens) - longest_match.b) + self._max_offs_delta
        right_a_pos = min(len(self._doc_tokens), right_a_pos)

        logging.debug("longest match: %s", longest_match)
        logging.debug("left_a_pos: %d", left_a_pos)
        logging.debug("right_a_pos: %d", right_a_pos)
        matcher.set_seq1(self._doc_tokens[left_a_pos:right_a_pos])

        matches = matcher.get_matching_blocks()
        if len(matches) == 1:
            return False
        logging.debug("all matches: %s", matches)

        ofs_diff = matches[-2].a + matches[-2].size - matches[0].a
        matched_length = sum(m.size for m in matches)

        logging.debug("text length: %d", len(tokens))
        logging.debug("ofs_diff: %d", ofs_diff)
        logging.debug("matched_length: %d", matched_length)

        if max(ofs_diff - self._max_offs_delta, 0) < len(tokens):
            if abs(len(tokens) - matched_length) <= self._max_length_delta:
                return True

        return False


    def is_sent_in_doc(self, tokens_or_sent):
        if not isinstance(tokens_or_sent, list):
            tokens = tok_sent(tokens_or_sent)
        else:
            tokens = tokens_or_sent
        text = u" ".join(tokens)
        if not text:
            raise RuntimeError("no tokens after text tokenization")
        logging.debug("stripped text: %s", text)
        #first approach
        pos = self._text.find(text)
        if pos != -1:
            return True
        logging.debug("failed to use dummy find, fallback to regexp")
        #approach from siv
        regexp = _gen_mega_regexp(text)
        m = regex.search(regexp, self._text, regex.UNICODE)
        if m is None:
            logging.debug("failed to use regexp, fallback to seq matching")
            return self._try_sequence_matcher(tokens)
        return True

# end doc operations



# extractor
class InvalidSubmission(Exception):
    pass

def extract_submission(arch_path, dest_dir):
    """raise InvalidSubmission if submission is malformed"""
    arc.Archive(arch_path, backend="patool").extractall(dest_dir)
    sources_dir = ""
    sources_list_file = ""

    for dirpath, dirnames, filenames in os.walk(dest_dir):
        for dirname in dirnames:
            if dirname.lower().find("sources") != -1:
                sources_dir = fs.join(dirpath, dirname)

        for filename in filenames:
            if filename.lower().find("sources_list") != -1:
                sources_list_file = fs.join(dirpath, filename)
                break

    if not sources_dir:
        raise InvalidSubmission("Не удалось обнаружить папку sources")

    if not sources_list_file:
        raise InvalidSubmission("Не удалось обнаружить файл sources_list.xlsx")

    return sources_dir, sources_list_file


#



def segtok_test():
    test_sent = u"простое предложение."
    without_mark_sent = u"простое предложение без знака"
    three_sents = u"простое предложение. «второе« 1990 предложение, (и т.д.). 2. почем"


    sents = seg.split_single(test_sent)
    print "|".join(s.encode("utf8") for s in sents)
    sents = seg.split_single(without_mark_sent)
    print "|".join(s.encode("utf8") for s in sents)
    sents = [s for s in seg.split_single(three_sents)]
    print u"|".join(sents)

    tokens = tok.space_tokenizer(sents[1])
    print "<>".join(s for s in tokens)

    tokens = tok.symbol_tokenizer(sents[1])
    print "<>".join(s for s in tokens if not ispunct(s))

    # tokens = tok.symbol_tokenizer(sents[1])
    # print "<>".join(s for s in tokens)
