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
from .v1 import processor as v1_proc


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

    def process_chunk(self, susp_id, chunk, sources):
        if chunk.get_mod_type() == ModType.ORIG:
            return
        source = sources[chunk.get_orig_doc_filename()]
        for sent in chunk.get_orig_sents():
            res = source.get_sent_offs(sent)
            for pipe in self._out_pipes:
                try:
                    pipe(susp_id, chunk.get_orig_doc_filename(),
                         chunk, res)
                except Exception as e:
                    logging.warning("Failed to send offsets to %s: %s", pipe.get_name(), e)

    def write_sources_to_files(self, susp_id, sources, out_dir):
        out_path = fs.join(out_dir, susp_id)
        if not fs.exists(out_path):
            os.makedirs(out_path)

        for src in sources:
            source_doc = sources[src]
            filepath = fs.join(out_path, src + ".txt")
            source_doc.write_text_to_file(filepath)

    def process_archive(self, archive_path, susp_id, version):

        temp_dir = tempfile.mkdtemp()
        try:

            sources_dir, meta_filepath = extract_submission(archive_path, temp_dir)

            if version == "1":
                chunks, _ = v1_proc.create_chunks(meta_filepath)
            elif version == "2":
                chunks = None
            else:
                raise RuntimeError("Unknown version: %s" % version)

            sources = load_sources_docs(sources_dir)

            self.write_sources_to_files(susp_id, sources, "src")
            for chunk in chunks:
                try:
                    self.process_chunk(susp_id, chunk, sources)
                except Exception as e:
                    logging.warning("Failed to process chunk %s: %s",
                                    chunk.get_chunk_id(), e)

        finally:
            shutil.rmtree(temp_dir)


    def process_submissions(self, version):
        entries = os.listdir(self._opts.subm_dir)
        for entry in entries:
            try:
                subm_dir= fs.join(self._opts.subm_dir, entry)
                susp_id = entry
                arc_path = glob.glob(subm_dir + "/*")
                if not arc_path:
                    logging.warning("empty submission dir %s", subm_dir)
                    continue
                if len(arc_path) > 1:
                    logging.warning("too many files (>1) in %s", subm_dir)
                    continue

                arc_path = arc_path[0].decode("utf8")
                self.process_archive(arc_path, susp_id, version)
            except Exception as e:
                logging.exception("Failed to process archive %s: %s", entry, e)


def gen(opts):
    pass
    # process_submissions(opts, "1")

def dumb_dump(opts):
    pipes = [DumbDumper()]
    gener = Generator(opts, pipes)
    gener.process_submissions(opts.version)

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
    dump_parser.set_defaults(func = dumb_dump)

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
    gener.process_archive(u"/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/148/148.zip", "148", "1")
    # process_archive("/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/024/024.tar", "1", "1")
    
    # process_archive(u"/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/039/Юсков - Сетевой маркетинг.rar", "039", "1")
