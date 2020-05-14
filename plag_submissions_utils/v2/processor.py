#!/usr/bin/env python
# coding: utf-8


import logging

import openpyxl
import xlrd

from plag_submissions_utils.common.processor import BasicProcessor
from plag_submissions_utils.common.processor import BasicProcesssorOpts
from plag_submissions_utils.common.errors import ErrSeverity
from plag_submissions_utils.common.errors import Error
from plag_submissions_utils.common.chunks import Chunk
from plag_submissions_utils.common.chunks import ChunkOpts
from plag_submissions_utils.common.chunks import ModType
from plag_submissions_utils.common.chunks import mod_types_to_str
import plag_submissions_utils.common.checkers as chks
import plag_submissions_utils.common.metrics as mtrks

class ProcessorOpts(BasicProcesssorOpts):
    def __init__(self):
        super(ProcessorOpts, self).__init__()
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
            ModType.ORIG : (0, 15),
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

def create_checkers(opts, sources_dir,
                    spell_checker_whitelist = None):
    return [
        chks.OriginalityChecker(opts),
        chks.OrigSentChecker(opts),
        chks.SourceDocsChecker(opts, sources_dir),
        chks.PRChecker(opts),
        chks.AddChecker(opts),
        chks.DelChecker(opts),
        chks.CPYChecker(opts),
        chks.CctChecker(opts),
        chks.SspChecker(opts),
        chks.SHFChecker(opts),
        chks.SYNChecker(opts),
        chks.LexicalSimChecker(opts),
        chks.ORIGModTypeChecker(),
        chks.SentCorrectnessChecker(),
        chks.CyrillicAlphabetChecker(opts),
        chks.SpellChecker(whitelist = spell_checker_whitelist)
    ]


def create_metrics(opts, sources_dir):
    metrics = [mtrks.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
               mtrks.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size),
               mtrks.SrcSentsCountMetric(opts.min_src_sents_cnt)]

    for mod_type in ModType.get_all_mod_types_v2():
        metrics.append(mtrks.ModTypeRatioMetric(mod_type,
                                                opts.mod_type_ratios[mod_type]))

    return metrics

class Processor(BasicProcessor):
    def _create_chunks(self, inp_file):
        return create_chunks(inp_file)

def _is_number_first_col(headers):
    return headers[0].lower().find("номер") != -1

def _check_headers(first_row):
    offs = 0
    if _is_number_first_col(first_row):
        offs = 1

    if first_row[0 + offs].lower().find("файла документа") == -1:
        return "Failed to find a column with source filename!"

    if first_row[1 + offs].lower().find("типы сокрытия") == -1:
        return "Failed to find a column with type of obfuscation!"

    if first_row[2 + offs].lower().find("эссе") == -1:
        return "Failed to find a column with modified text!"

    if first_row[3 + offs].lower().find("исходное предложение") == -1:
        return "Failed to find a column with original text!"

    return None

def create_chunks(inp_file, opts = ChunkOpts()):
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
    delete_first_column = _is_number_first_col(first_row)
    for rownum in range(1, sheet.nrows):
        row_vals = sheet.row_values(rownum)
        try:
            sent_num = rownum + 1
            if delete_first_column:
                row_vals = row_vals[1:]

            chunk = _try_create_chunk(
                row_vals,
                sent_num, opts)
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

def _get_filename(cell_value):
    #filename can be interpreted as float if the fullname is e.g. 1.html and ext is skipped.
    if isinstance(cell_value, float):
        return str(int(cell_value))
    return cell_value

def _try_create_chunk(row_vals, sent_num, opts):
    def check_str_cell(cell_val):
        if not isinstance(cell_val, str):
            raise RuntimeError("Sent # %d; Wrong value of the cell: %s"
                               % (sent_num, str(cell_val)))
        return cell_val


    orig_text = []
    #collect original text
    orig_text_col = 3
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

    mod_text = row_vals[2]
    if not mod_text:
        return None

    orig_doc = _get_filename(row_vals[0])
    mod_type_str = check_str_cell(row_vals[1])

    defined_cols = 0
    defined_cols += bool(orig_doc) + bool(mod_type_str) + bool(orig_text)

    if defined_cols != 0 and defined_cols != 3:
        raise RuntimeError("Неправильный формат!")

    return Chunk(mod_text = mod_text,
                 orig_text = orig_text,
                 orig_doc = orig_doc,
                 mod_type_str = mod_type_str,
                 chunk_num = sent_num,
                 opts = opts)


def chunk_to_row(chunk):
    mod_type_str = mod_types_to_str(chunk.get_all_mod_types())

    if mod_type_str == 'ORIG':
        mod_type_str = ''


    orig_colls = tuple(s for s in chunk.get_orig_sents())
    return (
        chunk.get_orig_doc_filename(),
        mod_type_str,
        chunk.get_mod_text(),
        ) + orig_colls

def create_xlsx_from_chunks(chunks, out_filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("название файла документа", "типы сокрытия", "эссе", "исходное предложение"))
    for chunk in chunks:
        ws.append(chunk_to_row(chunk))

    wb.save(filename = out_filename)
