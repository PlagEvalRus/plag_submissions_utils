#!/usr/bin/env bash

ansible-playbook ansible/local.yml -e proj_dir="$(pwd)"
