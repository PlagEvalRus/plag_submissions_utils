#!/usr/bin/env python
# coding: utf-8


import types
import logging
import re


import xlrd

from plag_submissions_utils.common.processor import BasicProcessor
from plag_submissions_utils.common.processor import BasicProcesssorOpts
from plag_submissions_utils.common.errors import ErrSeverity
from plag_submissions_utils.common.errors import Error
from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.chunks import ModType

class ProcessorOpts(BasicProcesssorOpts):
    def __init__(self, sources_dir, inp_file):
        super(ProcessorOpts, self).__init__(sources_dir, inp_file)
        self.min_src_docs      = 5
        self.min_sent_per_src  = 5
        self.min_sent_size     = 5
        self.min_real_sent_cnt = 50
        self.min_src_sents_cnt = 100
        self.mod_type_ratios   = {
            ModType.UNK : (0, 0),
            ModType.CPY : (0, 0),
            ModType.LPR : (10, 50),
            ModType.HPR : (10, 50),
            ModType.ORIG : (6, 15),
            ModType.DEL : (10, 40),
            ModType.ADD : (10, 40),
            ModType.CCT : (4, 20),
            ModType.SEP : (4, 20),
            ModType.SYN : (10, 40),
            ModType.SHF : (10, 40)
        }
        #допустимый процент изменений для каждого типа сокрытия
        self.diff_perc         = {
            ModType.CPY : (0, 0),
            ModType.LPR : (20, 100),
            ModType.HPR : (50, 100),
            ModType.ORIG : (100, 100),
            ModType.DEL : (15, 95),
            ModType.ADD : (15, 95),
            ModType.CCT : (0, 100),
            ModType.SEP : (0, 100),
            ModType.SYN : (30, 100),
            ModType.SHF : (20, 100)
        }

        self.min_lexical_dist = 25 #%
        self.min_originality = 0.77

class Processor(BasicProcessor):
    def __init__(self, opts, checkers,
                 metrics):
        super(Processor, self).__init__(opts, checkers,
                                        metrics)

    def _create_chunks(self):
        return create_chunks(self._opts.inp_file)

def _check_headers(first_row):
    if first_row[0].lower().find(u"номер") == -1:
        return "Failed to find a column with row number!"

    if first_row[1].lower().find(u"файла документа") == -1:
        return "Failed to find a column with source filename!"

    if first_row[2].lower().find(u"типы сокрытия") == -1:
        return "Failed to find a column with type of obfuscation!"

    if first_row[3].lower().find(u"эссе") == -1:
        return "Failed to find a column with modified text!"

    if first_row[4].lower().find(u"исходное предложение") == -1:
        return "Failed to find a column with original text!"

    return None

def _try_to_extract_sent_num(row_val):
    if isinstance(row_val, types.StringTypes):
        m = re.search(r"(\d+)", row_val)
        if m is None:
            raise RuntimeError("Failed to extract sent number from 0 column")
        return int(m.group(1))
    else:
        return int(row_val)

def create_chunks(inp_file):
    errors = []
    book = xlrd.open_workbook(inp_file)
    sheet = book.sheet_by_index(0)
    if sheet.nrows <= 2:
        errors.append(Error("Sheet contains 2 or less rows!!",
                            ErrSeverity.HIGH))
        return [], errors

    first_row = sheet.row_values(0)
    err = _check_headers(first_row)
    if err is not None:
        errors.append(Error(err,
                            ErrSeverity.HIGH))
        return [], errors

    chunks = []
    for rownum in range(1, sheet.nrows):
        row_vals = sheet.row_values(rownum)
        try:
            sent_num = _try_to_extract_sent_num(row_vals[0])
            chunk = _try_create_chunk(
                row_vals,
                sent_num)
            if chunk is None:
                continue
            logging.debug("parsed chunk: %s", chunk)
            chunks.append(chunk)
        except Exception as e:
            logging.exception("failed to create chunk: %s ", str(e))
            errors.append(Error("Не удалось проанализировать ряд с номером %d: %s" %
                                (rownum, str(e)),
                                ErrSeverity.HIGH))


    return chunks, errors


def _try_create_chunk(row_vals, sent_num):
    def check_str_cell(cell_val):
        if not isinstance(cell_val, (str, unicode)):
            raise RuntimeError("Sent # %d; Wrong value of the cell: %s"
                               % (sent_num, str(cell_val)))
        return cell_val


    orig_text = []
    #collect original text
    orig_text_col = 4
    while True:
        try:
            val = row_vals[orig_text_col]
        except IndexError:
            break
        if val:
            orig_text.append(check_str_cell(val))
            orig_text_col+=1
        else:
            break

    mod_text = row_vals[3]
    if not mod_text:
        return None

    orig_doc = row_vals[1]
    mod_type_str = check_str_cell(row_vals[2])

    defined_cols = 0
    defined_cols += bool(orig_doc) + bool(mod_type_str) + bool(orig_text)

    if defined_cols != 0 and defined_cols != 3:
        raise RuntimeError("Неправильный формат!")

    return Chunk(mod_text = mod_text,
                 orig_text = orig_text,
                 orig_doc = orig_doc,
                 mod_type_str = mod_type_str,
                 chunk_num = sent_num)
