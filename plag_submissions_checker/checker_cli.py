#!/usr/bin/env python
# coding: utf-8

import argparse

import logging

from . import common_runner


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", "-a", required=True)
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)

    try:

        metrics, errors, stat = common_runner.run(args.archive.decode("utf8"))

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
