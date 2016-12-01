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


def create_chunks(inp_file):
    errors = []
    book = xlrd.open_workbook(inp_file)
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
            sent_num = _try_to_extract_sent_num(rownum,
                                                main_content_offs == 1,
                                                row_vals[0])
            chunk = _try_create_chunk(
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

def _try_to_extract_sent_num(rownum, is_col_num_cell_found,
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

def _try_create_chunk(row_vals, sent_num, vals_offs):
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
