#!/bin/bash

base_path="$SUBMS_BASE_PATH"


if [  -z "$base_path" ]; then
    subm_path="$1"
    ./bin/submission_checker v2 -a "$subm_path"
    exit $?
fi

subm_dir="$1"
dir="submissions"
shopt -s extglob
./bin/submission_checker v2 -a $base_path/$dir/$subm_dir/*@(.rar|.zip)
