#!/bin/bash

# there's only one folder
cd /workspaces/*

# setup python and packages
pip install -r requirements-common.txt -r requirements-local.txt
