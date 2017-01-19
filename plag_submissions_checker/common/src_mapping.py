#!/usr/bin/env python
# coding: utf-8

import argparse
import logging
import csv
import hashlib

from .source_doc import find_src_paths

def gen_res_id(susp_id, src_filename):
    sha = hashlib.sha1(src_filename.encode("utf8"))
    doc_id = sha.hexdigest()[:16]
    return "{}:{}".format(susp_id, doc_id)


class Src(object):
    """Documentation for Src

    """
    def __init__(self, susp_id, src_filename,
                 src_path=None,
                 ext_id=None,
                 md5sum = None):
        super(Src, self).__init__()
        self._susp_id = susp_id
        self._src_filename = src_filename
        self._res_id = self._gen_res_id()
        self._md5sum = self._gen_md5sum(src_path) if src_path is not None else md5sum
        self._ext_id = ext_id

    def _gen_md5sum(self, src_path):
        hash_md5 = hashlib.md5()
        with open(src_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    def _gen_res_id(self):
        return gen_res_id(self._susp_id, self._src_filename)

    def get_ext_id(self):
        return self._ext_id

    def set_ext_id(self, ext_id):
        self._ext_id = ext_id

    def get_res_id(self):
        return self._res_id

    def to_csv_record(self):
        return '{},"{}",{},{},{}'.format(int(self._susp_id),
                                         self._src_filename.encode("utf8"),
                                         self._res_id, self._md5sum, self._ext_id)
class SrcMap(object):
    """Documentation for SrcMap

    """
    def __init__(self):
        self._srcs = {}

    def add(self, susp_id, src_filename, src_path, ext_id):
        src = Src(susp_id, src_filename, src_path, ext_id)
        self.update_src(src)

    def update_src(self, src):
        self._srcs[src.get_res_id()] = src

    def get_src_by_filename(self, susp_id, src_filename):
        return self._srcs[gen_res_id(susp_id, src_filename)]

    def get_src(self, res_id):
        try:
            return self._srcs[res_id]
        except KeyError:
            return None

    def to_csv(self, out):
        out.write("\n".join(s.to_csv_record() for s in self._srcs.viewvalues()))

    def from_csv(self, file_path):
        with open(file_path, 'r') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in reader:
                src = Src(str(row[0]).zfill(3),
                          row[1].decode("utf-8"),
                          md5sum = row[3], ext_id = row[4])
                self._srcs[src.get_res_id()] = src




def add_src_from_dir(susp_id, sources_dir, src_map,
                     use_filename_as_id = False):
    src_dict = find_src_paths(sources_dir)
    for num, src in enumerate(src_dict):
        if use_filename_as_id:
            ext_id = int(src)
        else:
            ext_id = (int(susp_id)<<6) + num

        src_map.add(susp_id, src,
                    src_dict[src],
                    ext_id)



def update_src_mapping(mapping_file, updates_file):
    mapping = SrcMap()
    mapping.from_csv(mapping_file)
    with open(updates_file, 'r') as f:
        for line in f:
            res_id, ext_id = line.strip().split(',')
            src = mapping.get_src(res_id)
            if src is None:
                continue
            src.set_ext_id(ext_id)
            mapping.update_src(src)

    with open(mapping_file, 'w') as f:
        mapping.to_csv(f)


#some cli

def update(opts):
    update_src_mapping(opts.input_mapping, opts.updates_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default = False)


    subparsers = parser.add_subparsers(help='sub-command help')

    update_parser = subparsers.add_parser('update', help='help of update')

    update_parser.add_argument("--updates_file", "-i", required=True,
                               help = "file with res_id and new ext_id")
    update_parser.add_argument("--input_mapping", "-m", default = "src_mapping.csv",
                               help = "src mapping file")
    update_parser.set_defaults(func = update)

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)
    try:

        args.func(args)
    except Exception as e:
        logging.exception("failed to update: %s ", e)


if __name__ == '__main__' :
    main()
