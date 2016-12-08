#!/bin/bash

subm_dir="$1"
base_path="/home/denin/Yandex.Disk/workspace/sci/plag/corpora/our_plag_corp"
dir="submissions"
shopt -s extglob
./bin/submission_checker v2 -a $base_path/$dir/$subm_dir/*@(.rar|.zip)

