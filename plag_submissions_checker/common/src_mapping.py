#!/usr/bin/env python
# coding: utf-8

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
        self._srcs[src.get_res_id()] = src

    def get_src_by_filename(self, susp_id, src_filename):
        return self._srcs[gen_res_id(susp_id, src_filename)]


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




def add_src_from_dir(susp_id, sources_dir, src_map):
    src_dict = find_src_paths(sources_dir)
    for num, src in enumerate(src_dict):
        src_map.add(susp_id, src,
                    src_dict[src],
                    (int(susp_id)<<6) + num)

