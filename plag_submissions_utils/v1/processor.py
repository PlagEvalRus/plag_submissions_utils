#!/usr/bin/env python
# coding: utf-8


import logging

import xlrd
import openpyxl

from plag_submissions_utils.common.processor import BasicProcessor
from plag_submissions_utils.common.processor import BasicProcesssorOpts
from plag_submissions_utils.common.errors import ErrSeverity
from plag_submissions_utils.common.errors import Error
from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.chunks import ChunkOpts
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.chunks import mod_type_to_str
import plag_submissions_utils.common.checkers as chks
import plag_submissions_utils.common.metrics as mtrks



class ProcessorOpts(BasicProcesssorOpts):
    def __init__(self):
        super(ProcessorOpts, self).__init__()
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
            ModType.HPR : (45, 99),
            ModType.ORIG : (100, 100),
            ModType.DEL : (15, 70),
            ModType.ADD : (15, 70),
            ModType.CCT : (0, 99),
            ModType.SSP : (0, 99)
        }


def create_checkers(opts, sources_dir):
    return [
        chks.OrigSentChecker(opts),
        chks.SourceDocsChecker(opts, sources_dir),
        chks.PRChecker(opts, fluctuation_delta = 5),
        chks.AddChecker(opts, fluctuation_delta = 5),
        chks.DelChecker(opts, fluctuation_delta = 5),
        chks.CPYChecker(opts, fluctuation_delta = 5),
        chks.CctChecker(opts, fluctuation_delta = 5),
        chks.SspChecker(opts, fluctuation_delta = 5),
        chks.ORIGModTypeChecker(),
        chks.SentCorrectnessChecker(),
        chks.SpellChecker(),
        chks.CyrillicAlphabetChecker(opts)
    ]

def create_metrics(opts, sources_dir):
    metrics = [mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
               mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]

    for mod_type in ModType.get_all_mod_types_v1():
        metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                opts.mod_type_ratios[mod_type],
                                                fluctuation_delta=5))
    return metrics


class Processor(BasicProcessor):
    def _create_chunks(self, inp_file):
        return create_chunks(inp_file)


def create_chunks(inp_file, opts = ChunkOpts()):
    errors = []
    book = xlrd.open_workbook(inp_file)
    sheet = book.sheet_by_index(0)
    if sheet.nrows <= 2:
        errors.append(Error("Sheet contains 2 or less rows!!",
                            ErrSeverity.HIGH))
        return [], errors

    #TODO find other columns; Do not use number column at all
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
            sent_num = rownum + 1
            chunk = _try_create_chunk(
                row_vals,
                sent_num,
                main_content_offs, opts)
            logging.debug("parsed chunk: %s", chunk)
            chunks.append(chunk)
        except Exception as e:
            logging.exception("failed to create chunk: %s ", str(e))
            errors.append(Error("Не удалось проанализировать ряд с номером %d: %s" %
                                (rownum, str(e)),
                                ErrSeverity.HIGH))


    return chunks, errors

def _try_create_chunk(row_vals, sent_num, vals_offs, opts):
    def check_str_cell(cell_val):
        if not isinstance(cell_val, (str, unicode)):
            raise RuntimeError("Sent # %d; Wrong value of the cell: %s"
                               % (sent_num, str(cell_val)))
        return cell_val

    return Chunk(mod_text = row_vals[vals_offs + 0],
                 orig_text = check_str_cell(row_vals[vals_offs + 1]),
                 orig_doc = row_vals[vals_offs + 2],
                 mod_type_str = check_str_cell(row_vals[vals_offs + 3]),
                 chunk_num = sent_num,
                 opts = opts)


def chunk_to_row(chunk):
    mod_type_str = mod_type_to_str(chunk.get_mod_type())

    if mod_type_str == 'ORIG':
        mod_type_str = ''

    return (
        chunk.get_mod_text(),
        chunk.get_orig_text(),
        chunk.get_orig_doc_filename(),
        mod_type_str)


def create_xlsx_from_chunks(chunks, out_filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("modified text", "original text", "src", "mod type"))
    for chunk in chunks:
        ws.append(chunk_to_row(chunk))

    wb.save(filename = out_filename)
