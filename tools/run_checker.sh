#!/bin/bash

subm_dir="$1"
# ./checker_cli.py -v -i examples/$subm_dir/sources_list.xlsx -s examples/$subm_dir/sources/
./bin/submission_checker   -a /home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp/submissions/$subm_dir/*.rar

