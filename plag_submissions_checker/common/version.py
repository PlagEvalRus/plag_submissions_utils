#!/usr/bin/env python
# coding: utf-8


def determine_version_by_id(susp_id):
    susp_id_int = int(susp_id)
    if 0 < susp_id_int < 2000:
        return "1"
    elif 2000 <= susp_id_int < 4000:
        return "2"
    else:
        raise RuntimeError("Invalid susp_id: %s" % susp_id)
