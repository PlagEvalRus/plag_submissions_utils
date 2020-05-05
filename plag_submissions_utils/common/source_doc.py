#!/usr/bin/env python
# coding: utf-8

import codecs
import os
import os.path as fs
import difflib

import logging


from . import text_proc

WHITELIST_EXTENSIONS = frozenset(['pdf', 'htm', 'html', 'txt', 'doc', 'docx', 'rtf', 'odt'])

def get_src_filename(path):
    basename = fs.basename(path).strip()
    name, ext = fs.splitext(basename)
    if not ext:
        return name
    if ext[1:].lower() in WHITELIST_EXTENSIONS:
        #this is good extension
        return name
    #otherwise its part of basename
    # logging.warning("Unknown extension: %s", ext)
    return basename


def find_src_paths(sources_dir):
    sources_dict = {}
    entries = os.listdir(sources_dir)
    for entry in entries:
        try:
            doc_path = fs.join(sources_dir, entry)
            doc_path = fs.abspath(doc_path)
            if not fs.isfile(doc_path):
                continue
            filename = get_src_filename(entry)
            if filename in sources_dict:
                logging.warning("source document with such filename %s already exists", filename)
            else:
                sources_dict[filename] = doc_path
        except Exception as e:
            logging.warning("failed to parse %s: %s", doc_path, e)

    return sources_dict


def load_sources_docs(sources_dir):
    paths_dict = find_src_paths(sources_dir)
    return {k:SourceDoc(paths_dict[k]) for k in paths_dict}


class SourceDoc(object):
    def __init__(self, doc_path, max_length_delta = 4,
                 max_offs_delta = 160):
        logging.debug("trying to parse %s", doc_path)
        # self._filename         = get_src_filename(doc_path)
        self._text             = text_proc.convert_doc(doc_path)
        self._text             = text_proc.preprocess_text(self._text)
        logging.debug("stripped source doc: %s", self._text)

        self._max_length_delta = max_length_delta
        self._max_offs_delta   = max_offs_delta

    def _try_sequence_matcher(self, sent):
        matcher = difflib.SequenceMatcher(a = self._text,
                                          b = sent,
                                          autojunk = False)
        #find seed
        longest_match = matcher.find_longest_match(0, len(self._text),
                                                   0, len(sent))

        #we should step back on the size of the prefix of the target sent (longest_match.b)
        #and we should step back on some extra size (max_offs_delta)
        left_a_pos = longest_match.a - (longest_match.b - 1) - self._max_offs_delta
        left_a_pos = max(0, left_a_pos)
        right_a_pos = longest_match.a + longest_match.size + (len(sent) - longest_match.b) + self._max_offs_delta
        right_a_pos = min(len(self._text), right_a_pos)

        logging.debug("longest match: %s", longest_match)
        logging.debug("left_a_pos: %d", left_a_pos)
        logging.debug("right_a_pos: %d", right_a_pos)
        matcher.set_seq1(self._text[left_a_pos:right_a_pos])

        matches = matcher.get_matching_blocks()
        if len(matches) == 1:
            return None
        logging.debug("all matches: %s", matches)

        offs_beg = left_a_pos + matches[0].a
        #matches[-1] is reserved by difflib creator
        offs_end = left_a_pos + matches[-2].a + matches[-2].size
        #how many letters between first matches and the last one.
        ofs_diff = offs_end - offs_beg
        matched_length = sum(m.size for m in matches)

        logging.debug("text length: %d", len(sent))
        logging.debug("ofs_diff: %d", ofs_diff)
        logging.debug("matched_length: %d", matched_length)

        if max(ofs_diff - self._max_offs_delta, 0) < len(sent):
            if abs(len(sent) - matched_length) <= self._max_length_delta:
                return (offs_beg, offs_end,
                        # this is count of erroneous symbols
                        # (ofs_diff - len(sent)) + (len(sent) - matched_length)
                        ofs_diff - matched_length)

        return None


    def is_sent_in_doc(self, sent):
        return self.get_sent_offs(sent) is not None

    def get_sent_offs(self, sent,
                      preproc_sent = True):

        text = sent
        if preproc_sent:
            text = text_proc.preprocess_text(text.strip())

        if not text:
            raise RuntimeError("no text left after text preprocessing")
        logging.debug("stripped text: %s", text)
        #first approach
        pos = self._text.find(text)
        if pos != -1:
            return (pos, pos + len(text), 0)

        logging.debug("failed to use literal find, fallback to seq matching")
        return self._try_sequence_matcher(text)



    # def get_filename(self):
    #     return self._filename

    def get_text(self):
        return self._text

    def write_text_to_file(self, file_path):
        with codecs.open(file_path, 'w', encoding="utf8", errors="strict") as f:
            f.write(self._text)
