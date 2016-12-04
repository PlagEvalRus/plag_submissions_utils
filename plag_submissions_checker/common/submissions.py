#!/usr/bin/env python
# coding: utf-8

import shutil
import tempfile
import os
import os.path as fs
import logging
import glob

from .extract_utils import extract_submission
from .version import determine_version_by_id

def run_over_submissions(subm_dir, arc_proc, limit_by_version = None):
    entries = os.listdir(subm_dir)
    for entry in entries:
        temp_dir = None
        try:
            arc_dir= fs.join(subm_dir, entry)
            susp_id = entry

            if limit_by_version is not None:
                if limit_by_version != determine_version_by_id(susp_id):
                    continue

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
