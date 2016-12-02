#!/bin/bash
export FLASK_APP='shire.py'
flask initdb
python shire.py
