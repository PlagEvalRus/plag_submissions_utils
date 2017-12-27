#!/usr/bin/env bash

set -e

docker run --rm -d --name submission_utils -p 8890:80 -v $(pwd):/var/www/submission_utils  plag/submissions_utils apache2ctl -DFOREGROUND
