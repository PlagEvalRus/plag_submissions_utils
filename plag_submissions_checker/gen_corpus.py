#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import os.path as fs
import logging
import tempfile
import shutil
import glob

from .common.chunks import ModType
from .common.extract_utils import extract_submission
from .common.source_doc import load_sources_docs
from .common import src_mapping
from .v1 import processor as v1_proc
from .v2 import processor as v2_proc


class DumbDumper(object):
    def __call__(self, susp_id, src_id, chunk, ofs_info):
        if ofs_info is None:
            b,e,er = -1,-1,-1
        else:
            b,e,er = ofs_info
        print "%s,%s,%d,%d,%d" % (susp_id, chunk.get_chunk_id(), b,e,er)

    def get_name(self):
        return 'DumbDumper'

class Generator(object):
    def __init__(self, opts, out_pipes):
        self._opts = opts
        self._out_pipes = out_pipes
        # if opts.mapping is not None:
        #     self._mapping = src_mapping.SrcMap()
        #     self._mapping.from_csv(opts.mapping)
        # else:
        #     self._mapping = create_mapping(opts.subm_dir)

    def process_chunk(self, susp_id, chunk, sources):
        if chunk.get_mod_type() == ModType.ORIG:
            return
        source = sources[chunk.get_orig_doc_filename()]
        for sent in chunk.get_orig_sents():
            res = source.get_sent_offs(sent)
            for pipe in self._out_pipes:
                try:
                    #TODO src id
                    pipe(susp_id, chunk.get_orig_doc_filename(),
                         chunk, res)
                except Exception as e:
                    logging.warning("Failed to send offsets to %s: %s", pipe.get_name(), e)

    def process_extracted_archive(self, susp_id, sources_dir, meta_filepath):
        if self._opts.version == "1":
            chunks, _ = v1_proc.create_chunks(meta_filepath)
        elif self._opts.version == "2":
            chunks, _ = v2_proc.create_chunks(meta_filepath)
        else:
            raise RuntimeError("Unknown version: %s" % self._opts.version)

        sources = load_sources_docs(sources_dir)

        for chunk in chunks:
            try:
                self.process_chunk(susp_id, chunk, sources)
            except Exception as e:
                logging.warning("Failed to process chunk %s: %s",
                                chunk.get_chunk_id(), e)

    def process_archive(self, archive_path, susp_id):

        temp_dir = tempfile.mkdtemp()
        try:
            sources_dir, meta_filepath = extract_submission(archive_path, temp_dir)
            self.process_extracted_archive(susp_id, sources_dir, meta_filepath)
        finally:
            shutil.rmtree(temp_dir)


    def process_submissions(self):
        run_over_submissions(self._opts.subm_dir, self.process_extracted_archive)

def run_over_submissions(subm_dir, arc_proc):
    entries = os.listdir(subm_dir)
    for entry in entries:
        temp_dir = None
        try:
            arc_dir= fs.join(subm_dir, entry)
            susp_id = entry
            arc_path = glob.glob(arc_dir + "/*")
            if not arc_path:
                logging.warning("empty submission dir %s", arc_dir)
                continue
            if len(arc_path) > 1:
                logging.warning("too many files (>1) in %s", arc_dir)
                continue

            arc_path = arc_path[0].decode("utf8")
            temp_dir = tempfile.mkdtemp()
            sources_dir, meta_filepath = extract_submission(arc_path, temp_dir)

            arc_proc(susp_id, sources_dir, meta_filepath)
        except Exception as e:
            logging.exception("Failed to process archive %s: %s", entry, e)
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir)


def write_sources_to_files(mapping, susp_id, sources, out_dir):
    if not fs.exists(out_dir):
        os.makedirs(out_dir)

    for src in sources:
        source_doc = sources[src]
        filepath = fs.join(
            out_dir,
            mapping.get_src_by_filename(susp_id, src).get_res_id() + ".txt")
        source_doc.write_text_to_file(filepath)



def create_mapping(subm_dir):
    mapping = src_mapping.SrcMap()

    def arc_proc(susp_id, sources_dir, _):
        src_mapping.add_src_from_dir(susp_id, sources_dir, mapping)

    run_over_submissions(subm_dir, arc_proc)
    return mapping

#cli support

def gen(opts):
    pass
    # process_submissions(opts, "1")

def dumb_dump(opts):
    pipes = [DumbDumper()]
    gener = Generator(opts, pipes)
    gener.process_submissions()

def gen_map(opts):
    mapping = create_mapping(opts.subm_dir)
    with open(opts.mapping_file, 'w') as f:
        mapping.to_csv(f)

def create_sources(opts):
    mapping = src_mapping.SrcMap()
    mapping.from_csv(opts.mapping)

    def arc_proc(susp_id, sources_dir, _):
        sources = load_sources_docs(sources_dir)
        write_sources_to_files(mapping, susp_id, sources, opts.out_dir)

    run_over_submissions(opts.subm_dir, arc_proc)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default = False)
    parser.add_argument("--version", "-V", required=True, help="version of essay")

    subparsers = parser.add_subparsers(help='sub-command help')

    gen_parser = subparsers.add_parser('gen',
                                       help='help of gen')

    gen_parser.add_argument("--subm_dir", "-i", required = True,
                            help = "directory with submissions")
    gen_parser.set_defaults(func = gen)

    dump_parser = subparsers.add_parser('dump',
                                        help='help of dump')

    dump_parser.add_argument("--subm_dir", "-i", required = True,
                             help = "directory with submissions")
    dump_parser.add_argument("--mapping", "-m", default=None,
                             help="mapping file. If it is not passed, it will be created!")
    dump_parser.set_defaults(func = dumb_dump)


    gen_map_parser = subparsers.add_parser('gen_map',
                                           help='help of gen_map')

    gen_map_parser.add_argument("--subm_dir", "-i", required = True,
                                help = "directory with submissions")
    gen_map_parser.add_argument("--mapping_file", "-o", default = "src_mapping.csv",
                                help = "mapping file path")
    gen_map_parser.set_defaults(func = gen_map)

    create_src_parser = subparsers.add_parser('create_src',
                                              help='help of create_src')

    create_src_parser.add_argument("--subm_dir", "-i", required = True,
                                   help = "directory with submissions")
    create_src_parser.add_argument("--mapping", "-m", default = "src_mapping.csv",
                                   help = "mapping file path")
    create_src_parser.add_argument("--out_dir", "-o", default="essay_src")
    create_src_parser.set_defaults(func = create_sources)
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
        self.version = "1"

def test():

    pipes = [DumbDumper()]
    gener = Generator(Opts(), pipes)
    gener.process_archive(u"/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/148/148.zip", "148")
    # process_archive("/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/024/024.tar", "1", "1")
    # process_archive(u"/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/039/Юсков - Сетевой маркетинг.rar", "039", "1")

def test_v2():
    pipes = [DumbDumper()]
    opts = Opts()
    opts.version = "2"
    gener = Generator(opts, pipes)
    gener.process_archive("data/test_data_v2/test.zip", "999")
