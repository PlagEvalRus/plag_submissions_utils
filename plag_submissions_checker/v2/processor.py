#!/usr/bin/env python
# coding: utf-8


import logging
import re


import xlrd

from plag_submissions_checker.common.processor import BasicProcessor
from plag_submissions_checker.common.processor import BasicProcesssorOpts
from plag_submissions_checker.common.errors import ErrSeverity
from plag_submissions_checker.common.errors import Error
from plag_submissions_checker.common.chunks import Chunk
from plag_submissions_checker.common.chunks import ModType

class ProcessorOpts(BasicProcesssorOpts):
    def __init__(self, sources_dir, inp_file):
        super(ProcessorOpts, self).__init__(sources_dir, inp_file)
        #TODO adjust params!!
        self.min_src_docs      = 5
        self.min_sent_per_src  = 4
        self.min_sent_size     = 5
        self.min_real_sent_cnt = 150
        self.mod_type_ratios   = {
            ModType.UNK : (0,0),
            ModType.CPY : (0, 10),
            ModType.LPR : (10, 30),
            ModType.HPR : (10, 20),
            ModType.ORIG : (0, 30),
            ModType.DEL : (20, 30),
            ModType.ADD : (15, 25),
            ModType.CCT : (5, 15),
            ModType.SSP : (5, 15)
        }
        #допустимый процент изменений для каждого типа сокрытия
        self.diff_perc         = {
            ModType.CPY : (0, 0),
            ModType.LPR : (23, 75),
            ModType.HPR : (45, 100),
            ModType.ORIG : (100, 100),
            ModType.DEL : (15, 70),
            ModType.ADD : (15, 70),
            ModType.CCT : (0, 80),
            ModType.SSP : (0, 85)
        }

class Processor(BasicProcessor):
    def __init__(self, opts, checkers,
                 metrics,
                 stat_collecter = None):
        super(Processor, self).__init__(opts, checkers,
                                        metrics, stat_collecter)

    def _create_chunks(self):
        return create_chunks(self._opts.inp_file)

def _check_headers(first_row):
    if first_row[0].lower().find(u"номер") == -1:
        return "Failed to find a column with row number!"

    if first_row[1].lower().find(u"файла документа") == -1:
        return "Failed to find a column with source filename!"

    if first_row[2].lower().find(u"типы сокрытия") == -1:
        return "Failed to find a column with type of obfuscation!"

    if first_row[3].lower().find(u"фрагменты текста эссе") == -1:
        return "Failed to find a column with modified text!"

    if first_row[4].lower().find(u"исходное предложение") == -1:
        return "Failed to find a column with original text!"

    return None

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
            sent_num = int(row_vals[0])
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

    return Chunk(mod_text = mod_text,
                 orig_text = orig_text,
                 orig_doc = row_vals[1],
                 mod_type_str = check_str_cell(row_vals[2]),
                 chunk_num = sent_num)
