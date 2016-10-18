#!/usr/bin/env python
# coding: utf-8

import argparse
import cgi
import cgitb
cgitb.enable()

import logging
import os.path as fs
import shutil
import tempfile

import sys

from jinja2 import Template


sys.path.append("/compiled/python")
from . import submission_checker_utils as scu


def print_resp(text):
    print "Content-Type: text/html; charset=utf-8"
    print
    print text.encode("utf-8")

def print_err(text):
    print "Status: 500 Internal error"
    print
    print text

def main():


    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO,
                        format = FORMAT)

    temp_dir = tempfile.mkdtemp()
    try:
        form = cgi.FieldStorage()

        if "file" not in form:
            print_err("no 'file' field in uploaded form")
            return
        upl_file_form = form["file"]
        upl_file_ext = fs.splitext(upl_file_form.filename)[1]

        arch_path = fs.join(temp_dir, "arch%s" % upl_file_ext)
        with open(arch_path, 'w') as f:
            f.write(upl_file_form.file.read())
            f.flush()

        opts = scu.PocesssorOpts(*scu.extract_submission(arch_path,
                                                         temp_dir))
        checkers = [scu.OrigSentChecker(opts),
                    scu.SourceDocsChecker(opts),
                    scu.PRChecker(opts),
                    scu.AddChecker(opts),
                    scu.DelChecker(opts),
                    scu.CPYChecker(opts),
                    scu.CctChecker(opts),
                    scu.SspChecker(opts)]
        metrics = [scu.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                   scu.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]
        for mod_type in scu.ModType.get_all_mods_type():
            metrics.append(scu.ModTypeRatioMetric(mod_type,
                                                  opts.mod_type_ratios[mod_type]))
        errors, stat = scu.Processor(opts, checkers, metrics).check()

        data_dir = \
        fs.dirname(fs.dirname(fs.realpath(__file__)))
        with open(fs.join(data_dir, "data/templates/report.html.j2"), 'r') as f:
            template = f.read()
        jinja_html_template = Template(template.decode("utf-8"))

        print_resp(jinja_html_template.render({
            "errors" : errors,
            "metrics": metrics
        }))

        # print "\n".join(str(e) for e in errors)
    except Exception as e:
        logging.exception("Error: %s", e)
        print_err(e)
    finally:
        # pass
        shutil.rmtree(temp_dir)

if __name__ == '__main__' :
    main()
