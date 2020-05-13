#!/usr/bin/env python
# coding: utf-8

import pipes
import subprocess
import os

import pymorphy2
import regex
from syntok.tokenizer import Tokenizer
import syntok._segmentation_states
#add common Russian abbrevations
SYNTOK_ORIG_ABBREV = syntok._segmentation_states.State.abbreviations
CYR_ABBREVS = frozenset(
    ['г', 'ул', 'д', 'кв', 'им',
     'см', 'мм', 'км', 'м', 'л',
     'янв', 'фев', 'мар', 'апр', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
     'пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс',
    ])
syntok._segmentation_states.State.abbreviations = (SYNTOK_ORIG_ABBREV | frozenset(CYR_ABBREVS))

SENTENCE_TERMINALS = syntok._segmentation_states.State.terminals
HYPHENS = [h for h in Tokenizer._hyphens if h is not '-']

import syntok.segmenter as seg

MORPH_ANALYZER = None
STOP_POS = ['PREP', 'CONJ', 'PRCL', 'INTJ']

def _get_morph_analyzer():
    global MORPH_ANALYZER
    if MORPH_ANALYZER is None:
        MORPH_ANALYZER = pymorphy2.MorphAnalyzer()
    return MORPH_ANALYZER


def ispunct(st):
    # return all(ch in string.punctuation for ch in st)
    return not st.isalnum()


def seg_text_as_list(text):
    # convert from generator to list
    return [s for s in seg_text(text)]

def seg_text(text):
    # text = text.strip()
    #clean all shitty \r\n and so on...
    # text = seg.to_unix_linebreaks(text)

    for paragraph in syntok.segmenter.process(text):
        for sent in paragraph:
            #skip newlines inside the sent
            sent_as_str = ''.join( (' ' if '\n' in t.spacing else t.spacing) + t.value
                                   for t in sent).lstrip()

            # sent_as_str += '\n'
            yield sent_as_str, sent

def _normalize(analyzer_results, token):
    if analyzer_results:
        norm = None
        if analyzer_results[0].tag.POS in ['PRTF', 'PRTS', 'GRND']:
            #https://pymorphy2.readthedocs.io/en/latest/user/guide.html#normalization
            norm = analyzer_results[0].inflect({'sing', 'nomn'})

        if norm is not None:
            return norm.word
        return analyzer_results[0].normal_form

    return token

def tok_sent(sent = None, tokens = None, make_lower = True, normalize = False,
             skip_stop_words = False):
    tok = Tokenizer()
    if tokens is None:
        tokens = tok.split(sent)

    if normalize or skip_stop_words:
        analyzer = _get_morph_analyzer()
        norm_tokens = []
        for token in tokens:
            results = analyzer.parse(token.value)
            normal_form = _normalize(results, token.value)
            if skip_stop_words and results:
                if results[0].tag.POS in STOP_POS:
                    continue

            norm_tokens.append(normal_form)
        tokens = norm_tokens
    else:
        tokens = [t.value for t in tokens]


    proc = lambda s : s
    if make_lower:
        proc = lambda s: s.lower()
    return [proc(s) for s in tokens if not ispunct(s)]

TIKA_PREFIX=os.environ.get("TIKA_PREFIX", "/compiled")

def convert_doc(doc_path):
    #tika's pdf converter is not very good
    if doc_path.endswith("pdf"):
        cmd = "pdftotext %s -" % pipes.quote(doc_path)
    elif doc_path.endswith("txt"):
        cmd = "enca -Lrussian -x utf-8 %s && cat %s" % ((pipes.quote(doc_path), )*2)
    else:
        cmd = "%s/bin/tika --text %s" % (TIKA_PREFIX, pipes.quote(doc_path))
    # textract html converter is not very good
    # cmd = "textract %s" % pipes.quote(doc_path)
    text = subprocess.check_output(cmd, shell=True)
    return text.decode("utf8")

def preprocess_text(text):
    for hyphen in HYPHENS:
        text = text.replace(hyphen, "\u002d")

    #remove unnecessary \n inside sentences
    text = "\n".join(s for s, _ in seg_text(text))

    #remove double spaces '  ' or ' \t' and non-breaking spaces
    text = " ".join(p for p in regex.split(r'\p{Blank}', text) if p)
    return text
