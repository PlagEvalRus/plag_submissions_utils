#!/usr/bin/env bash

set -e


docker run -d --name submission_utils -p 8889:80 -v $(pwd):/var/www/submission_utils  plag/submissions_utils apache2ctl -DFOREGROUND
