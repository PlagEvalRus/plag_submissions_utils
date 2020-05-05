#!/usr/bin/env python
# coding: utf-8

import os
import re
import collections
import argparse
import logging
import shutil

from yandex_translate import YandexTranslate

from .common.chunks import ModType
from .common.source_doc import load_sources_docs
from .common.submissions import run_over_submissions
from .common import text_proc
from .common.translated_chunks import TranslatedChunk
from . import common_runner
from .v3.processor import create_xlsx_from_chunks



#TODO
class TransStat(object):
    def __init__(self):
        self.src_cnt = 0
        self.total_chars = 0
        self.chars_to_translate = 0
        self.translated_chars = 0
        self.other_lang_total_chars = 0


    def __str__(self):
        return "sources: %d, total chars: %d, chars_to_translate: %d"\
            " translated chars: %d, other lang chars: %d" % (
                self.src_cnt, self.total_chars, self.chars_to_translate,
                self.translated_chars, self.other_lang_total_chars
            )




class TextForTrans(object):
    def __init__(self, text, chunk = None, offs_tuple = None):
        self.text = text
        self.translated_text = ''
        self.chunk = chunk
        self.offs_beg = offs_tuple[0]
        self.offs_end = offs_tuple[1]
        self.err_symbols = offs_tuple[2]


    def __str__(self):
        return "ChunkId %s; src offs beg %d, end %d, err %d;text:\n %s" % (
            self.chunk.get_id() if self.chunk else None,
            self.offs_beg, self.offs_end, self.err_symbols,
            self.text.encode('utf8')
        )

class YandexTranslator(object):
    def __init__(self, opts):
        self._from = 'ru'
        self._to = 'en'
        #10k request limit
        self._max_chars = 9500
        self._lang = '%s-%s' % (self._from, self._to)
        with open(opts.ya_key_file, 'r') as f:
            key = f.read()
        self._yatrans = YandexTranslate(key)

    def _trans_batch(self, text_for_trans_list):
        try:

            resp = self._yatrans.translate([t.text for t in text_for_trans_list],
                                           self._lang)
            if len(resp['text']) != len(text_for_trans_list):
                raise RuntimeError("Resp and Req sizes mismatch!")
            for tinfo, ts in zip(text_for_trans_list, resp['text']):
                tinfo.translated_text = ts
        except Exception as e:
            logging.error("Failed to process batch (size %d): %s", len(text_for_trans_list), str(e))





    def translate(self, text_for_trans_list):
        batch = []
        cur_chars = 0

        for text_info in text_for_trans_list:
            if cur_chars + len(text_info.text) > self._max_chars:
                if cur_chars == 0:
                    raise RuntimeError("Too large block (%d) for even one request!" %
                                       len(text_info.text))
                self._trans_batch(batch)
                cur_chars = 0
                batch = []

            batch.append(text_info)
            cur_chars += len(text_info.text)

        if batch:
            self._trans_batch(batch)



class Translator(object):
    def __init__(self, opts):
        self._opts = opts
        self._stat = TransStat()
        self._yatrans = YandexTranslator(opts)

    def _process_chunk(self, chunk, sources, sources_map):
        if chunk.get_mod_type() == ModType.ORIG:
            return

        source_id = chunk.get_orig_doc_filename()

        if not source_id:
            #it may be original too but with unknown mod_type
            return

        source = sources[source_id]
        for sent_num, sent in enumerate(chunk.get_orig_sents()):
            sent_text = text_proc.preprocess_text(sent.strip())
            res = source.get_sent_offs(sent_text, preproc_sent = False)
            if res is None:
                logging.warning("Chunk %d, sent %d: unable to find sent in sources",
                                chunk.get_id(), sent_num)
                continue
            sources_map[source_id].append( TextForTrans(sent_text, chunk, res) )


    def _process_extracted_archive(self, susp_id, sources_dir, meta_file_path):
        chunks, chunks_errors = common_runner.create_chunks(susp_id, meta_file_path,
                                                            self._opts.version)

        if chunks_errors:
            logging.error("Id: %s - Errors while creating chunks:\n%s", susp_id,
                          "\n".join(str(e) for e in chunks_errors))
        sources = load_sources_docs(sources_dir)
        sources_map = collections.defaultdict(lambda : [])
        for chunk in chunks:
            try:
                self._process_chunk(chunk, sources, sources_map)
            except Exception as e:
                logging.exception("Id: %s - Failed to process chunk %s: %s",
                                  susp_id, chunk, e)

        self._add_original_texts(sources, sources_map)
        if self._opts.save_src_blocks_dir:
            self._save_sources(susp_id, sources_map,
                               self._opts.save_src_blocks_dir,
                               save_translated_text = False)

        self._translate_sources(susp_id, sources_map)


        original_chunks = [c for c in chunks if c.get_mod_type() == ModType.ORIG or \
                           not c.get_orig_doc_filename() ]
        self._make_submission_archive(susp_id, sources_map, original_chunks)


    def _create_trans_chunk(self, chunk, orig = False):
        trans_chunk = TranslatedChunk(orig_text = [],
                                      mod_text = chunk.get_mod_sents(),
                                      mod_type_str = '',
                                      orig_doc = chunk.get_orig_doc(),
                                      chunk_num = chunk.get_id(),
                                      translator_type_str = 'Yandex' if not orig else 'original',
                                      translated_text = [])

        trans_chunk.set_mod_types(chunk.get_all_mod_types())
        return trans_chunk


    def _make_submission_archive(self, susp_id, sources_map, original_chunks):
        self._save_sources(susp_id, sources_map, self._opts.out_dir,
                           save_translated_text = True)

        chunks_dict = {c.get_id(): self._create_trans_chunk(c, orig=True) for c in original_chunks}
        for source_id, text_for_trans_list in sources_map.items():
            for tinfo in text_for_trans_list:
                if tinfo.chunk is None:
                    continue
                chunk = tinfo.chunk
                if chunk.get_id() not in chunks_dict:
                    chunks_dict[chunk.get_id()] = self._create_trans_chunk(chunk)

                trans_chunk = chunks_dict[chunk.get_id()]

                assert source_id == trans_chunk.get_orig_doc_filename(), \
                    "One chunk from different sources!"

                #we write translated to original to mimic the Translated Essays structure,
                # where original text is in English and the translated one is in Russian.
                trans_chunk.get_orig_sent_holder().add_sent(tinfo.translated_text, tokenize = False)
                trans_chunk.get_translated_sent_holder().add_sent(tinfo.text, tokenize = False)

        translated_chunks = list(chunks_dict.values())
        translated_chunks.sort(key = lambda c : c.get_id())
        susp_dir = os.path.join(self._opts.out_dir, susp_id)
        create_xlsx_from_chunks(translated_chunks,
                                os.path.join(susp_dir, 'sources_list.xlsx'))
        shutil.make_archive(susp_dir, 'gztar', susp_dir)
        shutil.rmtree(susp_dir)
        os.makedirs(susp_dir)
        shutil.move(os.path.join(self._opts.out_dir, '%s.tar.gz' % susp_id), susp_dir)






    def _translate_sources(self, susp_id, sources_map):
        if self._opts.dry_run:
            for _, text_for_trans_list in sources_map.items():
                for num, t in enumerate(text_for_trans_list):
                    self._stat.translated_chars += len(t.text)
                    pref = 'W/o chunk '
                    if t.chunk is not None:
                        pref = 'W/ chunk %d ' % t.chunk.get_id()
                    t.translated_text = pref + "trans_%d. " % num
            return

        for source_id, text_for_trans_list in sources_map.items():
            logging.info("Translating: susp %s, src %s", susp_id, source_id)
            self._yatrans.translate(text_for_trans_list)
            for text_info in text_for_trans_list:
                self._stat.chars_to_translate += len(text_info.text)
                if text_info.translated_text:
                    self._stat.translated_chars += len(text_info.text)
                    self._stat.other_lang_total_chars += len(text_info.translated_text)



    def _save_sources(self, susp_id, sources_map, base_out_dir,
                      save_translated_text = True):
        out_dir = os.path.join(base_out_dir, susp_id, 'sources')
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        for source_id, text_for_trans_list in sources_map.items():
            with open(os.path.join(out_dir, '%s.txt' % source_id), 'w') as outf:
                text_for_trans_list.sort(key = lambda t : t.offs_beg)
                for t in text_for_trans_list:
                    if save_translated_text:
                        text = t.translated_text
                    else:
                        text = t.text
                    outf.write("%s\n" % text.encode('utf8'))


    def _add_original_texts(self, sources, sources_map):
        """add text from sources for translation that was not used in an essay
        """
        for source_id, text_for_trans_list in sources_map.items():
            if source_id not in sources:
                continue
            if not text_for_trans_list:
                logging.warning("For source %s no text was reused in essay", source_id)
                continue
            source = sources[source_id]
            self._stat.src_cnt += 1
            self._stat.total_chars += len(source.get_text())
            self._add_original_texts_for_source(source, text_for_trans_list)




    def _add_original_texts_for_source(self, source, text_for_trans_list):
        source_text = source.get_text()
        text_for_trans_list.sort(key = lambda t : t.offs_beg)

        new_text_blocks = []

        def _add_block(offs_beg, offs_end):
            # nonlocal new_text_blocks
            block_size = offs_end - offs_beg
            if block_size > self._opts.min_block_size:
                #remove excessive blank lines
                text = re.sub(r'\n\s*\n', '\n\n', source_text[offs_beg:offs_end])
                new_text_blocks.append(TextForTrans(text,
                                                    offs_tuple = (offs_beg, offs_end, 0)))

        cur_offs = 0
        for reused_text_info in text_for_trans_list:
            real_offs = max(cur_offs, reused_text_info.offs_beg - self._opts.max_block_size)
            logging.debug("curr_offs: %d; real_offs: %d", cur_offs, real_offs)
            _add_block(real_offs, reused_text_info.offs_beg)
            cur_offs = reused_text_info.offs_end + 1

        #handle text after the last reused source block
        text_len = len(source_text)
        end_offs = min(text_len, cur_offs + self._opts.max_block_size)
        _add_block(cur_offs, end_offs)

        logging.debug("Added %d new text blocks", len(new_text_blocks))
        text_for_trans_list.extend(new_text_blocks)




    def process_submissions(self):
        if self._opts.ids_file:
            with open(self._opts.ids_file, 'r') as f:
                ids = frozenset([int(l) for l in f])
        else:
            ids = None
        run_over_submissions(self._opts.subm_dir,
                             self._process_extracted_archive,
                             self._opts.limit_by_version,
                             include_ids_set = ids)

        logging.info("Stat: %s", self._stat)



def translate_cli(opts):
    translator = Translator(opts)
    translator.process_submissions()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default = False)

    parser.add_argument("--version", "-V", default=None,
                        help="version of essay."
                        " If it is not specified, will be determined by essay id.")
    parser.add_argument("--limit_by_version", "-L", default=None,
                        help="process only essays with specified version."
                        "If not specified, process all found essays.")

    subparsers = parser.add_subparsers(help='sub-command help')

    trans_parser = subparsers.add_parser('trans',
                                         help='help of trans')

    trans_parser.add_argument("--subm_dir", "-i", required = True,
                              help = "directory with submissions")
    trans_parser.add_argument("--ids_file", "-I", default='',
                              help = "translate only those ids, otherwise process everything")
    trans_parser.add_argument("--out_dir", "-o", required = True)
    trans_parser.add_argument("--max_block_size", "-s", default=8000, type=int)
    trans_parser.add_argument("--min_block_size", "-m", default=42, type=int)
    trans_parser.add_argument("--save_src_blocks_dir", "-S", default='',
                              help='Path to dir. Useful for debug and total size estimation')
    trans_parser.add_argument("--dry_run", "-d", default=False, action='store_true',
                              help="Do not invoke MT service.")
    trans_parser.add_argument("--ya_key_file", "-k", required=True,
                              help="Yandex translate API key.")

    trans_parser.set_defaults(func = translate_cli)

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)
    try:

        args.func(args)
    except Exception as e:
        logging.exception("failed to translate_cli: %s ", e)


if __name__ == '__main__' :
    main()
