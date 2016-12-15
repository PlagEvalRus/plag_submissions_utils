#!/usr/bin/env python
# coding: utf-8

import logging
import string


#stolen from http://www.uni-weimar.de/medien/webis/events/pan-12/pan12-code/pan12-text-alignment-baseline.py

DELETECHARS = ''.join([string.punctuation, string.whitespace])
def _tokenize(text, length):
    """ Tokeniz a given text and return a dict containing all start and end
    positions for each token.
    Characters defined in the global string DELETECHARS will be ignored.

    Keyword arguments:
    text   -- the text to tokenize
    length -- the length of each token
    """
    tokens = {}
    token = []

    for i in range(0, len(text)):
        if text[i] not in DELETECHARS:
            token.append((i, text[i]))
        if len(token) == length:
            ngram = ''.join([x[1].lower() for x in token])
            if ngram not in tokens:
                tokens[ngram] = []
            tokens[ngram].append((token[0][0], token[-1][0]))
            token = token[1:]

    return tokens

class SimpleDetectorOpts(object):
    """Documentation for SimpleDetectorOpts

    """
    def __init__(self, lenght=50):
        super(SimpleDetectorOpts, self).__init__()
        self.lenght = lenght


class SimpleDetector(object):
    """Documentation for Checker

    """

    def __init__(self, opts = SimpleDetectorOpts()):
        super(SimpleDetector, self).__init__()
        self._opts = opts

    def __call__(self, susp_text, src_text):
        susp_tokens = _tokenize(susp_text, self._opts.lenght)
        logging.debug("suspicious tokens: %s", susp_tokens)

        detections = []
        skipto = -1
        token = []
        for i in range(0, len(src_text)):
            if i > skipto:
                if src_text[i] not in DELETECHARS:
                    token.append((i, src_text[i]))
                if len(token) == self._opts.lenght:
                    ngram = ''.join([x[1].lower() for x in token])
                    logging.debug("generated ngram: %s", ngram)
                    if ngram in susp_tokens:
                        d = ((token[0][0],token[-1][0]),
                             (susp_tokens[ngram][0][0],
                              susp_tokens[ngram][0][1]))
                        for t in susp_tokens[ngram]:
                            start_src = token[0][0]
                            start_susp = t[0]
                            while (start_susp < len(susp_text) and
                                   start_src < len(src_text) and
                                   src_text[start_src] == susp_text[start_susp]):
                                start_susp = start_susp + 1
                                start_src = start_src + 1
                                while (start_susp < len(susp_text) and
                                       susp_text[start_susp] in DELETECHARS):
                                    start_susp = start_susp + 1
                                while (start_src < len(src_text) and
                                       src_text[start_src] in DELETECHARS):
                                    start_src = start_src + 1
                            if (start_src - 1) - token[0][0] > d[0][1] - d[0][0]:
                                d = ((token[0][0], start_src), (t[0], start_susp))
                        detections.append(d)
                        skipto = d[0][1]
                        if skipto < len(src_text):
                            token = [(skipto, src_text[skipto])]
                        else:
                            break
                    else:
                        token = token[1:]

        logging.debug("%d fragments were detected!", len(detections))
        logging.debug("\n".join(str(d) for d in detections))
        return detections

def calc_originality_by_detections(detections, susp_text):
    if not susp_text:
        return 0.0
    detected_text = sum(det[1][1] - det[1][0] for det in detections)

    return 1.0 - float(detected_text) / len(susp_text)

def calc_originality(susp_text, src_text, detector = None):
    if detector is None:
        detector = SimpleDetector()
    detections = detector(susp_text, src_text)
    return calc_originality_by_detections(detections, susp_text)
