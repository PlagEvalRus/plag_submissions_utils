#!/usr/bin/env python
# -*- coding:utf-8 -*-



import argparse
import logging

import os.path as fs
import os

#import operator
#import itertools

import xlrd
#python-Levenshtein package
from Levenshtein import distance

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
        return  "%s for sent %d: %s" %(pref, self.chunk_num, self.msg)

class ModType(object):
    UNK = 0
    CPY = 1
    LPR = 2
    HPR = 3

class Chunk(object):
    def __init__(self, orig_sent, mod_sent, 
                 mod_type, orig_doc, chunk_num):
        self.chunk_num     = chunk_num
        self.original_sent = orig_sent
        self.modified_sent = mod_sent
        self.mod_type      = mod_type
        self.orig_doc      = orig_doc
    
    

# checkers

class IChecher(object):
    def get_errors(self):
        raise NotImplementedError("should implement this!")
    
    def __call__(self, chunk):
        raise NotImplementedError("should implement this!")

class PRQualChecker(IChecher):
    def __init__(self, opts):
        self._opts = opts
        self._errors = []
        
    def get_errors(self):
        return self._errors
    
    def __call__(self, chunk):
        if chunk.mod_type != ModType.LPR and chunk.mod_type != ModType.HPR:
            return
        
        logging.debug("chunk.mod_type %d" %chunk.mod_type)
        min_diff = 0.0
        max_diff = 0.0
        if chunk.mod_type == ModType.LPR:
            min_diff = self._opts.lpr_min_diff
            max_diff = self._opts.lpr_max_diff
        elif chunk.mod_type == ModType.HPR:
            min_diff = self._opts.hpr_min_diff
            max_diff = 1.0
            
        d = distance(chunk.original_sent, chunk.modified_sent)
        max_len = max(len(chunk.original_sent), len(chunk.modified_sent))
        diff_perc = float(d) / max_len
        
        logging.debug("for sent %d: %f " % (chunk.chunk_num, diff_perc))
        
        if diff_perc < min_diff:
            self._errors.append(ChunkError("diff is too low %f:" % diff_perc, 
                                           chunk.chunk_num))
        elif diff_perc > max_diff:
            self._errors.append(ChunkError("diff is too high %f:" % diff_perc,
                                           chunk.chunk_num,
                                           ErrSeverity.LOW))


class SourceDocsChecker(IChecher):
    def __init__(self, opts):
        super(SourceDocsChecker, self).__init__()
        self._opts = opts
        self._used_source_docs_set = set()
        self._errors = []
        
        self._found_sources_docs = self._init_sources_dict() 
        
    def _get_filename(self, path):
        try:
            return fs.splitext(path)[0].decode("utf-8")
        except Exception as e:
            return fs.splitext(path)[0]
        
    def _init_sources_dict(self):
        sources_dict = {}
        entries = os.listdir(self._opts.sources_dir)
        for entry in entries:
            doc_path = fs.join(self._opts.sources_dir, entry)
            filename = self._get_filename(entry)
            if filename in sources_dict:
                self._errors.append(Error("duplication of source documents", ErrSeverity.HIGH))
            else:
                sources_dict[filename] = doc_path
        return sources_dict
        
    def _check_existance(self, orig_doc):
        filename = self._get_filename(orig_doc)
        return filename in self._found_sources_docs
        #path = fs.join(self._opts.sources_dir, orig_doc)
        #return fs.exists(path)
    
    def get_errors(self):
        if len(self._used_source_docs_set) < self._opts.min_source_cnt:
            self._errors.append(Error("sources count is too low", ErrSeverity.HIGH))
            
        return self._errors
    
    def __call__(self, chunk):
        if not chunk.orig_doc:
            return
        
        if chunk.orig_doc not in self._used_source_docs_set:
            self._used_source_docs_set.add(chunk.orig_doc)
            
            if not self._check_existance(chunk.orig_doc):
                self._errors.append(ChunkError("file %s does not exist " % chunk.orig_doc.encode("utf-8"),
                                               chunk.chunk_num))


class Processor(object):
    def __init__(self, opts, checkers):
        self._opts = opts
        
        self._checkers = checkers
    
    def _create_mod_type(self, mod_str):
        mls = mod_str.lower()
        if mls == "cpy":
            return ModType.CPY
        elif mls == "lpr":
            return ModType.LPR
        elif mls == "hpr":
            return ModType.HPR
        else:
            return ModType.UNK
        
    
    def _try_create_chunk(self, row_vals):
        #throw if there is non-number
        sent_num = int(row_vals[0])
        
        return Chunk(mod_sent = row_vals[1], 
                     orig_sent = row_vals[2],
                     orig_doc = row_vals[3],
                     mod_type = self._create_mod_type(row_vals[4]),
                     chunk_num = sent_num)
    
    def _process_chunk(self, chunk):
        
        for checker in self._checkers:
            try:
                checker(chunk)
            except Exception as e:
                logging.exception("during proc %d: " % chunk.chunk_num)
        
            
    
    def check(self):
        book = xlrd.open_workbook(self._opts.inp_file)
        sheet = book.sheet_by_index(0)
        for rownum in range(sheet.nrows):
            row_vals = sheet.row_values(rownum)
            
            try:
                chunk = self._try_create_chunk(row_vals)
                #logging.info("type orig_sent %s, type mod_sent %s " % (type(chunk.original_sent),
                #                                                       type(chunk.modified_sent)))
                self._process_chunk(chunk)
            except Exception as e:
                logging.exception("failed to create chunk: %s " % str(e))
        
        errors = []
        for checker in self._checkers:
            errors.extend(str(e) for e in checker.get_errors())
        
        logging.error("\n".join(errors)) if errors else 42
      
        
        
        
        

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--inp_file", "-i", required=True, 
                        help="config")
    parser.add_argument("--sources_dir", "-s", required=True)
    parser.add_argument("--min_source_cnt", "-m", default=5, type=int)
    parser.add_argument("--lpr_min_diff", default=0.08, type=float)
    parser.add_argument("--lpr_max_diff", default=0.3, type=float)
    parser.add_argument("--hpr_min_diff", default=0.3, type=float)
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)

    checkers = [ SourceDocsChecker(args),
                 PRQualChecker(args)]
    Processor(args, checkers).check()

            


    
    
if __name__ == '__main__' :
    main()
    #test()
 
