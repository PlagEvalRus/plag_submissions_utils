#!/usr/bin/env python
# coding: utf-8

import logging
import sys
import os.path as fs

sys.path.insert(0,
                fs.dirname(fs.dirname(fs.realpath(__file__))))

import plag_submissions_utils.checker_cgi as cc


if __name__ == '__main__':
    cc.main()
