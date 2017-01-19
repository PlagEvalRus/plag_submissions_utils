#!/usr/bin/env python
# coding: utf-8

import os
import os.path as fs

import pyunpack as arc

class InvalidSubmission(Exception):
    pass

def extract_submission(arch_path, dest_dir):
    """raise InvalidSubmission if submission is malformed"""
    arc.Archive(arch_path, backend="patool").extractall(dest_dir)
    sources_dir = ""
    sources_list_file = ""

    for dirpath, dirnames, filenames in os.walk(dest_dir):
        for dirname in dirnames:
            if dirname.lower().find("sources") != -1:
                sources_dir = fs.join(dirpath, dirname)

        for filename in filenames:
            if filename.lower().find("sources_list") != -1:
                sources_list_file = fs.join(dirpath, filename)
                break

    if not sources_dir:
        raise InvalidSubmission("Не удалось обнаружить папку sources")

    if not sources_list_file:
        raise InvalidSubmission("Не удалось обнаружить файл sources_list.xlsx")

    return sources_dir, sources_list_file
