#!/usr/bin/env python
# coding: utf-8


# import os
import os.path as fs
import sys
import glob

sys.path.insert(0,
                fs.dirname(fs.dirname(fs.realpath(__file__))))

import plag_submissions_utils.common_runner as cr
from plag_submissions_utils.common.version import determine_version_by_id

results=[("id", "fatal", "serious", "medium")]
if len(sys.argv) == 1:
    print "<data_dir> [ids_list]"

data_dir=sys.argv[1]
if len(sys.argv) == 3:
    ids_list_path=sys.argv[2]
else:
    ids_list_path = None

if ids_list_path is None:
    glob_path = data_dir + "/*"
    ids = [fs.basename(p) for p in glob.glob(glob_path)]
else:
    with open(ids_list_path, 'r') as f:
        ids = [l.strip() for l in f]

for sid in ids:
    glob_path=data_dir + "/" + str(sid).zfill(3) + "/*"

    expanded_path=glob.glob(glob_path)
    if not expanded_path:
        continue

    arch_path = expanded_path[0].decode("utf8")
    try:
        version = determine_version_by_id(sid)
        metrics, errors, stat = cr.run(arch_path, version)
        results.append(
            (sid,
             cr.fatal_errors_cnt(metrics, errors, stat),
             cr.serious_errors_cnt(metrics, errors, stat),
             cr.medium_errors_cnt(metrics, errors, stat,
                                  count_metrics=False)))
    except Exception as e:
        print "failed to process %s: %s" % (sid, e)

results.sort(key= lambda r : r[0])
print "\n".join(["%s,%s,%s,%s"%res for res in results])
