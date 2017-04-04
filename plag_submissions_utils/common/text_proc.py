#!/usr/bin/env python
# coding: utf-8

import pipes
import subprocess

import segtok.segmenter as seg
import segtok.tokenizer as tok
import regex

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

    #some documents contain "заповеди Пифагора.Нравственные"
    # or "психотерапии . Они"
    #regex supports unicode uppercase letters - \p{Lu}
    text = regex.sub(ur"(\p{Ll})\s?\.\s?(\p{Lu})", ur"\1. \2", text)
    return seg.split_multi(text)

def tok_sent(sent):
    tokens = tok.symbol_tokenizer(sent)
    return [s.lower() for s in tokens if not ispunct(s)]

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
    text = text.replace(u"\u2010", u"\u002d")
    text = text.replace(u"\u00ad", u"\u002d")

    #remove unnecessary \n inside sentences
    text_spans = seg.rewrite_line_separators(
        seg.to_unix_linebreaks(text),
        seg.MAY_CROSS_ONE_LINE)
    text = u"".join(text_spans)

    #remove double spaces '  ' or ' \t' and non-breaking spaces
    text = u" ".join(p for p in regex.split(ur'\p{Blank}', text) if p)
    return text
