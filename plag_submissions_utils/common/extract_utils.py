#!/usr/bin/env python
# coding: utf-8

import os
import os.path as fs

import pyunpack as arc

class InvalidSubmission(Exception):
    pass

def _skip_file(filename):
    if filename.startswith(".") or \
       filename.startswith("~"):
        return True
    return False

def extract_submission(arch_path, dest_dir):
    """raise InvalidSubmission if submission is malformed"""
    arc.Archive(arch_path, backend="patool").extractall(dest_dir)
    sources_dir = ""
    sources_list_file = ""

    for dirpath, dirnames, filenames in os.walk(dest_dir):
        if fs.basename(dirpath) == "__MACOSX":
            continue

        for dirname in [d for d in dirnames if not _skip_file(d)]:
            if dirname.lower().find("sources") != -1:
                sources_dir = fs.join(dirpath, dirname)

        for filename in [f for f in filenames if not _skip_file(f)]:
            if filename.lower().find("sources_list") != -1:
                sources_list_file = fs.join(dirpath, filename)
                break

    if not sources_dir:
        raise InvalidSubmission("Не удалось обнаружить папку sources")

    if not sources_list_file:
        raise InvalidSubmission("Не удалось обнаружить файл sources_list.xlsx")

    return sources_dir, sources_list_file
