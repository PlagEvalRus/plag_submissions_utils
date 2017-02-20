#!/usr/bin/env python
# coding: utf-8

import random

def generate_end_of_sentence(max_new_lines):
    #Exponential distribution; mean is 0.4
    new_lines_cnt = int(round(random.expovariate(1/0.4)))
    new_lines_cnt = min(max_new_lines, new_lines_cnt)
    if new_lines_cnt > 0:
        suffix = "\n" * new_lines_cnt
    else:
        suffix = " "
    return suffix
