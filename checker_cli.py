#!/usr/bin/env python
# coding: utf-8

import argparse

import logging
import shutil
import tempfile

import plag_submissions_checker.submission_checker_utils as scu


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", "-a", required=True)
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    FORMAT="%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format = FORMAT)

    temp_dir = tempfile.mkdtemp()
    try:

        #TODO: parse opts from config
        opts = scu.PocesssorOpts(*scu.extract_submission(args.archive.decode("utf8"),
                                                         temp_dir))
        checkers = [scu.OrigSentChecker(opts),
                    scu.SourceDocsChecker(opts),
                    scu.PRChecker(opts),
                    scu.AddChecker(opts),
                    scu.DelChecker(opts),
                    scu.CPYChecker(opts),
                    scu.CctChecker(opts),
                    scu.SspChecker(opts),
                    scu.ORIGModTypeChecker()]
        metrics = [scu.SrcDocsCountMetric(opts.min_src_docs, opts.min_sent_per_src),
                scu.DocSizeMetric(opts.min_real_sent_cnt, opts.min_sent_size)]
        for mod_type in scu.ModType.get_all_mods_type():
            metrics.append(scu.ModTypeRatioMetric(mod_type,
                                                  opts.mod_type_ratios[mod_type]))
        errors, stat = scu.Processor(opts, checkers, metrics).check()

        print "Статистика"
        for m in metrics:
            print "%s %s"  % ("!" * m.get_violation_level(), m)

        print
        print "Ошибки"
        print "\n".join(str(e) for e in errors)
    except Exception as e:
        logging.exception("Error: %s", e)
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__' :
    main()
