#!/usr/bin/env python
# coding: utf-8

import argparse

import logging

from . import common_runner

def run_v1(opts):
    return common_runner.run(opts.archive.decode("utf8"), "1")

def run_v2(opts):
    return common_runner.run(opts.archive.decode("utf8"), "2")

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

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)

    try:

        metrics, errors, stat = args.func(args)

        print "Статистика"
        for m in metrics:
            print "%s %s"  % ("!" * m.get_violation_level(), m)

        print
        print "Ошибки"
        print "\n".join(str(e) for e in errors)
    except Exception as e:
        logging.exception("Error: %s", e)

if __name__ == '__main__' :
    main()
