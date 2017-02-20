#!/usr/bin/env python
# coding: utf-8

import argparse
import sys

import logging

from . import common_runner
from .common.submissions import run_over_submissions
from .common.stat import StatCollector
from .common.stat import print_mod_types_stat

def run_v1(opts):
    common_run(opts, "1")

def run_v2(opts):
    common_run(opts, "2")

def common_run(opts, version):
    metrics, errors, stat = common_runner.run(opts.archive.decode("utf8"), version)

    print "Статистика"
    for m in metrics:
        print "%s %s"  % ("!" * m.get_violation_level(), m)

    print
    print "Ошибки"
    print "\n".join(str(e) for e in errors)


def collect_stat(opts):
    stat_collector = StatCollector()
    def proc_arc(susp_id, _, meta_file_path):
        chunks, _ = common_runner.create_chunks(
            susp_id, meta_file_path)
        stat_collector(chunks)

    run_over_submissions(opts.archive_dir, proc_arc)
    print_mod_types_stat(stat_collector, sys.stdout)



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")

    subparsers = parser.add_subparsers(help='different versions')

    v1_parser = subparsers.add_parser('v1', help='help of set')

    v1_parser.add_argument("--archive", "-a", required=True)
    v1_parser.set_defaults(func = run_v1)

    v2_parser = subparsers.add_parser('v2', help='help of set')

    v2_parser.add_argument("--archive", "-a", required=True)
    v2_parser.set_defaults(func = run_v2)

    stat_parser = subparsers.add_parser('stat')
    stat_parser.add_argument("--archive_dir", "-d", required=True)
    stat_parser.set_defaults(func = collect_stat)

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)

    try:
        args.func(args)

    except Exception as e:
        logging.exception("Error: %s", e)

if __name__ == '__main__' :
    main()
