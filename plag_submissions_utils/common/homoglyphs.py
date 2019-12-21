#!/usr/bin/env python
# coding: utf-8


import copy

from confusable_homoglyphs.categories import alias
from confusable_homoglyphs.confusables import confusables_data
#adapted from the confusable_homoglyphs

# http://unicode.org/reports/tr39/

def _find_confusable(init_char, preferred_aliases, max_transitive_depth = 1):
    depth = 0
    chars = [init_char]
    while depth <= max_transitive_depth:
        depth += 1
        found = []
        for char in chars:
            t = confusables_data.get(char, False)
            if t is not False:
                found.extend(t)

        chars = []
        for d in found:
            aliases = [alias(glyph) for glyph in d['c']]
            for a in aliases:
                if a in preferred_aliases:
                    return {'c': d['c'], 'a': a}

            chars.append(d['c'])

    return {}

def find_homoglyphs(string, preferred_aliases):
    preferred_aliases = [a.upper() for a in preferred_aliases]
    outputs = []
    cache = {}
    for num, char in enumerate(string):
        if char in cache:
            d = copy.copy(cache[char])
            d['pos'] = num
            outputs.append(d)
            continue
        char_alias = alias(char)
        if char_alias in preferred_aliases:
            continue

        t = _find_confusable(char, preferred_aliases)
        if t :
            outputs.append({
                'character': char,
                'alias': char_alias,
                'homoglyphs': t,
                'pos': num
            })
    return outputs
