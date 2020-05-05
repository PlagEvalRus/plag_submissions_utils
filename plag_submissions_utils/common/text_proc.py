#!/usr/bin/env python
# coding: utf-8

import pipes
import subprocess

import segtok.segmenter as seg
import segtok.tokenizer as tok
import pymorphy2
import regex

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
    text = text.strip()
    #clean all shitty \r\n and so on...
    text = seg.to_unix_linebreaks(text)

    # This cases are supported by segtok-2 (syntok)
    #TODO migrate to python3 and syntok
    text = regex.sub(r"\b(\d+)г.?\s", r"\1 г. ", text)

    #some documents contain "заповеди Пифагора.Нравственные"
    # or "психотерапии . Они"
    #regex supports unicode uppercase letters - \p{Lu}
    text = regex.sub(r"(\p{Ll})\s?\.\s?(\p{Lu})", r"\1. \2", text)
    return seg.split_multi(text)

def _normalize(analyzer_results, token):
    if analyzer_results:
        norm = None
        if analyzer_results[0].tag.POS in ['PRTF', 'PRTS', 'GRND']:
            #https://pymorphy2.readthedocs.io/en/latest/user/guide.html#normalization
            norm = analyzer_results[0].inflect({'sing', 'nomn'})

        if norm is not None:
            return norm.word
        else:
            return analyzer_results[0].normal_form
    else:
        return token

def tok_sent(sent, make_lower = True, normalize = False,
             skip_stop_words = False):
    tokens = tok.symbol_tokenizer(sent)

    if normalize or skip_stop_words:
        analyzer = _get_morph_analyzer()
        norm_tokens = []
        for token in tokens:
            results = analyzer.parse(token)
            normal_form = _normalize(results, token)
            if skip_stop_words and results:
                if results[0].tag.POS in STOP_POS:
                    continue

            norm_tokens.append(normal_form)
        tokens = norm_tokens


    proc = lambda s : s
    if make_lower:
        proc = lambda s: s.lower()
    return [proc(s) for s in tokens if not ispunct(s)]

def convert_doc(doc_path):
    #tika's pdf converter is not very good
    if doc_path.endswith("pdf"):
        cmd = "pdftotext %s -" % pipes.quote(doc_path)
    elif doc_path.endswith("txt"):
        cmd = "enca -Lrussian -x utf-8 %s && cat %s" % ((pipes.quote(doc_path), )*2)
    else:
        cmd = "/compiled/bin/tika --text %s" % pipes.quote(doc_path)
    # textract html converter is not very good
    # cmd = "textract %s" % pipes.quote(doc_path)
    text = subprocess.check_output(cmd, shell=True)
    return text.decode("utf8")

def preprocess_text(text):
    #convert various unicode hyphens
    text = text.replace("\u2010", "\u002d")
    text = text.replace("\u00ad", "\u002d")

    #remove unnecessary \n inside sentences
    text_spans = seg.rewrite_line_separators(
        seg.to_unix_linebreaks(text),
        seg.MAY_CROSS_ONE_LINE)
    text = "".join(text_spans)

    #remove double spaces '  ' or ' \t' and non-breaking spaces
    text = " ".join(p for p in regex.split(r'\p{Blank}', text) if p)
    return text
