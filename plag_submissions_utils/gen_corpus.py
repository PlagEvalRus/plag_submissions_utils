#!/usr/bin/env python
# coding: utf-8

import argparse
import collections
from xml.etree import ElementTree as ET
import xml.dom.minidom
import json
import os
import os.path as fs
import logging
import tempfile
import shutil
import sys

from .common.chunks import ModType
from .common.chunks import mod_types_to_str
from .common.extract_utils import extract_submission
from .common.source_doc import load_sources_docs
from .common import src_mapping
from .common.submissions import run_over_submissions
from . import common_runner


class DummyWriter(object):
    def write(self, _):
        pass


class SrcRetrievalMetaGenerator(object):
    def __init__(self, opts):
        self._opts = opts
        if opts.mapping is not None:
            self._mapping = src_mapping.SrcMap()
            self._mapping.from_csv(opts.mapping)
        else:
            self._mapping = create_mapping(opts.subm_dir,
                                           use_filename_as_id = opts.use_filename_as_id)

        self._src_map = None
        self._init_src_map()

        if not fs.exists(opts.src_retr_out_dir):
            os.makedirs(opts.src_retr_out_dir)

    def _init_src_map(self):
        self._src_map = collections.defaultdict(lambda: 0)

    def __call__(self, susp_doc, chunk, ofs_info):
        if ofs_info is None:
            return

        susp_id = susp_doc.get_susp_id()
        src_id = self._mapping.get_src_by_filename(
            susp_id,
            chunk.get_orig_doc_filename()).get_ext_id()

        self._src_map[src_id] += len(chunk.get_modified_sents())

    def on_susp_end(self, susp_doc):
        #TODO lang
        #TODO version
        susp_id = susp_doc.get_susp_id()
        meta = {"language": "ru",
                "plagiarism": [],
                "suspicious-document": "%s.txt" % susp_id}

        for src_id in self._src_map:
            if self._src_map[src_id] < self._opts.min_sent_cnt:
                continue
            meta["plagiarism"].append({
                "reused_sent_cnt": self._src_map[src_id],
                "id": src_id
            })

        self._init_src_map()


        out_path = fs.join(
            self._opts.src_retr_out_dir,
            "%s.json" % susp_id)
        with open(out_path, 'w') as out:
            json.dump(meta, out,
                      indent=4, separators=(',', ': '))



    def get_name(self):
        return 'SrcRetrievalMetaGenerator'


class TextAlignmentMetaGenerator(object):
    def __init__(self, opts):
        self._opts = opts
        if opts.mapping is not None:
            self._mapping = src_mapping.SrcMap()
            self._mapping.from_csv(opts.mapping)
        else:
            self._mapping = create_mapping(opts.subm_dir,
                                           use_filename_as_id = opts.use_filename_as_id)

        self._xml_map = {}
        self._pairs = []

        if not fs.exists(opts.text_align_out_dir):
            os.makedirs(opts.text_align_out_dir)
        if fs.exists(fs.join(self._opts.text_align_out_dir, "pairs")):
            os.remove(fs.join(self._opts.text_align_out_dir, "pairs"))


    def __call__(self, susp_doc, chunk, ofs_info):
        if ofs_info is None:
            return

        susp_id = susp_doc.get_susp_id()
        src_id = self._mapping.get_src_by_filename(
            susp_id,
            chunk.get_orig_doc_filename()).get_ext_id()

        susp_filename = susp_id + ".txt"
        src_filename = src_id + ".txt"
        if src_id not in self._xml_map:
            #TODO add version
            self._xml_map[src_id] = ET.Element('document', reference=susp_filename)
            self._pairs.append((susp_filename, src_filename))

        src_offs_beg, src_offs_end,err = ofs_info

        e = ET.Element('feature',
                       name='plagiarism',
                       this_offset=str(susp_doc.get_offs_for_text(chunk.get_chunk_id())),
                       this_length=str(len(chunk.get_mod_text())),
                       source_reference=src_filename,
                       source_offset=str(src_offs_beg),
                       source_length=str(src_offs_end - src_offs_beg),
                       type="manual",
                       obfuscation=mod_types_to_str(chunk.get_all_mod_types()),
                       #TODO
                       this_language="ru",
                       source_language="ru",
                       txt_extraction_err=str(err))
        self._xml_map[src_id].append(e)


    def _get_as_xml(self, src_id):
        return self._xml_map[src_id]

    def _finalize_pair(self, susp_id, src_id):
        meta_xml = self._get_as_xml(src_id)
        ugly_xml_str = ET.tostring(meta_xml, 'utf-8')

        ugly_xml = xml.dom.minidom.parseString(ugly_xml_str)

        pretty_xml = ugly_xml.toprettyxml()

        out_path = fs.join(
            self._opts.text_align_out_dir,
            "suspicious-document%s-source-document%s.xml" % (susp_id, src_id))
        with open(out_path, 'w') as out:
            out.write(pretty_xml)

    def on_susp_end(self, susp_doc):
        #TODO
        #self._join_adjacent_chunks()
        susp_id = susp_doc.get_susp_id()
        for src_id in self._xml_map:
            self._finalize_pair(susp_id, src_id)
        self._xml_map = {}
        #update pairs
        with open(fs.join(self._opts.text_align_out_dir, "pairs"), 'a') as f:
            for pair in self._pairs:
                f.write("%s %s\n" % pair)
        self._pairs = []


    def get_name(self):
        return 'TextAligmentMetaGenerator'


class DumbDumper(object):
    def __init__(self, out_path = None):
        if out_path is None:
            self._out = sys.stdout
        else:
            self._out = open(out_path, 'w')

    def __call__(self, susp_doc, chunk, ofs_info):
        if ofs_info is None:
            b,e,er = -1,-1,-1
        else:
            b,e,er = ofs_info
        self._out.write("%s,%s,%d,%d,%d\n" % (susp_doc.get_susp_id(),
                                              chunk.get_chunk_id(), b,e,er))

    def on_susp_end(self, susp_doc):
        pass

    def get_name(self):
        return 'DumbDumper'

class Generator(object):
    def __init__(self, opts, out_pipes):
        self._opts = opts
        self._out_pipes = out_pipes

    def process_chunk(self, susp_doc, chunk, sources):
        if chunk.get_mod_type() == ModType.ORIG:
            return
        source = sources[chunk.get_orig_doc_filename()]
        for sent in chunk.get_orig_sents():
            res = source.get_sent_offs(sent)
            for pipe in self._out_pipes:
                try:
                    pipe(susp_doc, chunk, res)
                except Exception as e:
                    logging.warning("Id: %s - Failed to send offsets to %s: %s",
                                    susp_doc.get_susp_id(), pipe.get_name(), e)

    def process_extracted_archive(self, susp_id, sources_dir, meta_file_path):
        chunks, chunks_errors = common_runner.create_chunks(susp_id, meta_file_path,
                                                            self._opts.version)

        if chunks_errors:
            logging.error("Id: %s - Errors while creating chunks:\n%s", susp_id,
                          "\n".join(str(e) for e in chunks_errors))
        sources = load_sources_docs(sources_dir)
        susp_doc = SuspDocGenerator(susp_id, DummyWriter())
        susp_doc.add_chunks(chunks)
        for chunk in chunks:
            try:
                self.process_chunk(susp_doc, chunk, sources)
            except Exception as e:
                logging.warning("Id: %s - Failed to process chunk %s: %s",
                                susp_id, chunk.get_chunk_id(), e)

        for pipe in self._out_pipes:
            try:
                pipe.on_susp_end(susp_doc)
            except Exception as e:
                logging.warning("Id: %s - Failed to finalize susp: %s",
                                susp_doc.get_susp_id(), e)

    def process_archive(self, archive_path, susp_id):

        temp_dir = tempfile.mkdtemp()
        try:
            sources_dir, meta_file_path = extract_submission(archive_path, temp_dir)
            self.process_extracted_archive(susp_id, sources_dir, meta_file_path)
        finally:
            shutil.rmtree(temp_dir)


    def process_submissions(self):
        run_over_submissions(self._opts.subm_dir,
                             self.process_extracted_archive,
                             self._opts.limit_by_version)


class SuspDocGenerator(object):
    """Documentation for SuspDocGenerator

    """
    def __init__(self, susp_id, out):
        super(SuspDocGenerator, self).__init__()
        self._susp_id = susp_id
        self._out = out
        self._cur_offset = 0
        self._offsets_dict = {}

    def get_susp_id(self):
        return self._susp_id

    def add_text(self, text_id, text):

        suffix = '\n'
        self._out.write(text.encode("utf-8") + suffix)
        text_offs = self._cur_offset
        self._offsets_dict[text_id] = text_offs
        self._cur_offset += len(text) + len(suffix)
        return text_offs

    def get_offs_for_text(self, text_id):
        return self._offsets_dict[text_id]

    def add_chunks(self, chunks):
        for chunk in chunks:
            self.add_text(chunk.get_chunk_id(),
                          chunk.get_mod_text())

def write_sources_to_files(mapping, susp_id, sources, out_dir,
                           ext_id_as_filename = False):
    if not fs.exists(out_dir):
        os.makedirs(out_dir)

    for src_filename in sources:
        source_doc = sources[src_filename]
        src = mapping.get_src_by_filename(susp_id, src_filename)
        if ext_id_as_filename:
            filename = src.get_ext_id()
        else:
            filename = src.get_res_id()
        filepath = fs.join(
            out_dir, filename + ".txt")
        source_doc.write_text_to_file(filepath)



def create_mapping(subm_dir, limit_by_version = None,
                   use_filename_as_id = False):
    mapping = src_mapping.SrcMap()

    def arc_proc(susp_id, sources_dir, _):
        src_mapping.add_src_from_dir(susp_id, sources_dir, mapping,
                                     use_filename_as_id)

    run_over_submissions(subm_dir, arc_proc, limit_by_version)
    return mapping

#cli support

def create_text_align_meta(opts):
    pipes = [TextAlignmentMetaGenerator(opts)]
    gener = Generator(opts, pipes)
    gener.process_submissions()

def create_src_retr_meta(opts):
    pipes = [SrcRetrievalMetaGenerator(opts)]
    gener = Generator(opts, pipes)
    gener.process_submissions()

def create_pan_meta(opts):
    pipes = [SrcRetrievalMetaGenerator(opts),
             TextAlignmentMetaGenerator(opts)]
    gener = Generator(opts, pipes)
    gener.process_submissions()


def dumb_dump(opts):
    pipes = [DumbDumper(opts.out_file)]
    gener = Generator(opts, pipes)
    gener.process_submissions()

def gen_map(opts):
    mapping = create_mapping(opts.subm_dir, opts.limit_by_version,
                             opts.use_filename_as_id)
    with open(opts.mapping_file, 'w') as f:
        mapping.to_csv(f)

def create_sources(opts):
    mapping = src_mapping.SrcMap()
    mapping.from_csv(opts.mapping)

    def arc_proc(susp_id, sources_dir, _):
        sources = load_sources_docs(sources_dir)
        write_sources_to_files(mapping, susp_id, sources, opts.out_dir,
                               opts.ext_id_as_filename)

    run_over_submissions(opts.subm_dir, arc_proc, opts.limit_by_version)

def create_susp_docs(opts):
    def arc_proc(susp_id, _, meta_file_path):
        chunks, _ = common_runner.create_chunks(
            susp_id, meta_file_path, opts.version)
        out_path = fs.join(opts.out_dir, "%s.txt" % susp_id)
        with open(out_path, 'w') as f:
            susp_gen = SuspDocGenerator(susp_id, f)
            susp_gen.add_chunks(chunks)
    if not fs.exists(opts.out_dir):
        os.makedirs(opts.out_dir)

    run_over_submissions(opts.subm_dir, arc_proc, opts.limit_by_version)


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

    dump_parser = subparsers.add_parser('dump',
                                        help='help of dump')

    dump_parser.add_argument("--subm_dir", "-i", required = True,
                             help = "directory with submissions")
    dump_parser.add_argument("--out_file", "-o", default=None)

    dump_parser.set_defaults(func = dumb_dump)


    gen_map_parser = subparsers.add_parser('gen_map',
                                           help='help of gen_map')

    gen_map_parser.add_argument("--subm_dir", "-i", required = True,
                                help = "directory with submissions")
    gen_map_parser.add_argument("--mapping_file", "-o", default = "src_mapping.csv",
                                help = "mapping file path")
    gen_map_parser.add_argument("--use_filename_as_id", "-u", action='store_true')

    gen_map_parser.set_defaults(func = gen_map)

    create_src_parser = subparsers.add_parser('create_src',
                                              help='help of create_src')

    create_src_parser.add_argument("--subm_dir", "-i", required = True,
                                   help = "directory with submissions")
    create_src_parser.add_argument("--mapping", "-m", default = "src_mapping.csv",
                                   help = "mapping file path")
    create_src_parser.add_argument("--out_dir", "-o", default="essay_src")
    create_src_parser.add_argument("--ext_id_as_filename", "-e", action="store_true")
    create_src_parser.set_defaults(func = create_sources)

    create_susp_parser = subparsers.add_parser('create_susp',
                                               help='help of create_susp')
    create_susp_parser.add_argument("--subm_dir", "-i", required = True,
                                    help = "directory with submissions")
    create_susp_parser.add_argument("--out_dir", "-o", default="essay_susp")
    create_susp_parser.set_defaults(func = create_susp_docs)

    text_align_parser = subparsers.add_parser('text_align',
                                              help='help of text_align')
    text_align_parser.add_argument("--subm_dir", "-i", required = True,
                                   help = "directory with submissions")
    text_align_parser.add_argument("--text_align_out_dir", "-o",
                                   default="01-manual-plagiarism")
    text_align_parser.add_argument("--mapping", "-m", default = "src_mapping.csv",
                                   help = "mapping file path")
    text_align_parser.add_argument("--use_filename_as_id", "-u", action='store_true')
    text_align_parser.set_defaults(func = create_text_align_meta)

    src_retr_parser = subparsers.add_parser('src_retr',
                                            help='help of src_retr')
    src_retr_parser.add_argument("--subm_dir", "-i", required = True,
                                 help = "directory with submissions")
    src_retr_parser.add_argument("--src_retr_out_dir", "-o", default="src_retrieval")
    src_retr_parser.add_argument("--mapping", "-m", default = "src_mapping.csv",
                                 help = "mapping file path")
    src_retr_parser.add_argument("--min_sent_cnt", "-s", default=4, type=int)
    src_retr_parser.add_argument("--use_filename_as_id", "-u", action='store_true')
    src_retr_parser.set_defaults(func = create_src_retr_meta)

    pan_parser = subparsers.add_parser('pan',
                                       help='help of pan')
    pan_parser.add_argument("--subm_dir", "-i", required = True,
                            help = "directory with submissions")
    pan_parser.add_argument("--mapping", "-m", default = "src_mapping.csv",
                            help = "mapping file path")
    pan_parser.add_argument("--src_retr_out_dir", "-s", default="src_retrieval")
    pan_parser.add_argument("--min_sent_cnt", "-c", default=4, type=int)
    pan_parser.add_argument("--use_filename_as_id", "-u", action='store_true')
    pan_parser.add_argument("--text_align_out_dir", "-t",
                            default="01-manual-plagiarism")
    pan_parser.set_defaults(func = create_pan_meta)
    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)
    try:

        args.func(args)
    except Exception as e:
        logging.exception("failed to gen: %s ", e)


if __name__ == '__main__' :
    main()

class Opts(object):
    def __init__(self):
        self.version = None

def test():

    pipes = [DumbDumper()]
    gener = Generator(Opts(), pipes)
    gener.process_archive("data/test_data/test.zip", "4")

def test_v2():
    pipes = [DumbDumper()]
    gener = Generator(Opts(), pipes)
    gener.process_archive("data/test_data_v2/test.zip", "2000")
