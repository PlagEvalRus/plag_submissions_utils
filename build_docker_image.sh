#!/bin/bash

set -e

devel="$1"

#That command creates build_exactus_info container
ansible-playbook ansible/docker.yml

#commit this container to image
docker commit build_submissions_utils plag/submissions_utils

if [ -z "$devel" ]; then
    docker rm -f build_submissions_utils
fi
